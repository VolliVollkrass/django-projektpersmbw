"""Hochrechnung der Jahres-Personalkosten eines Einsatzes.

Rechnet die Monatsmatrix Januar–Dezember nach, wie sie das Excel-Hochrechnungs-
tool des LKA ermittelt (Blatt „Hochrechnung“):

- Grundbezug aus der zum Monatsersten gültigen Besoldungstabelle × Umfang
- OFZ: kinderlos → Stufe L/V; mit Kindern → komplette „Kind n“-Spalte
  (Kind 1 = Stufe 1, Kind 2 = Stufe 2, Kind 3 = Stufe 2 + Zuschlag 3. Kind,
  jedes weitere Kind + „je weiterem Kind“) × Umfang
- Strukturzulage für A 9 – A 13 × Umfang
- Jährliche Sonderzahlung im Dezember: Jahressumme der Bezüge / 12 × Faktor
  (bis A 11: 70 %, ab A 12: 65 % – wie IFS-Formel im Tool)
- Beihilfe nach Beihilfe-Art des Mitarbeiters (Tarif 830 altersabhängig,
  Tarif 814 pauschal, freiwillig gesetzlich = manuelle Beträge + KV-Zuschuss)
- Versorgungsumlage = (Bezüge inkl. Sonderzahlung) × Satz der Einrichtung

Hinweis: Die Erhöhungsbeträge je Kind für A 8 – A 10 rechnet das Excel-Tool
NICHT mit ein; das ist hier bewusst genauso (Klärung mit Fachbereich offen).
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from .models import (
    Beihilfesatz,
    Besoldungsbetrag,
    Besoldungstabelle,
    Familienzuschlagtabelle,
    Zulagensatz,
)

ZWEI_STELLEN = Decimal("0.01")

# Jährliche Sonderzahlung in Prozent des Monatsbezugs (Excel: IFS über die
# Besoldungsgruppe; unterhalb A 9 dort nicht definiert -> wie A 9 behandelt)
SONDERZAHLUNG_AB_A12 = Decimal("0.65")
SONDERZAHLUNG_BIS_A11 = Decimal("0.70")

STRUKTURZULAGE_GRUPPEN = {"A9", "A10", "A11", "A12", "A13"}

MONATSNAMEN = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]


class KalkulationsFehler(Exception):
    """Fachliche Angaben fehlen oder Tabellenstände sind unvollständig."""


def _sonderzahlung_faktor(gruppe):
    try:
        nummer = int(gruppe[1:])
    except (TypeError, ValueError):
        return SONDERZAHLUNG_BIS_A11
    return SONDERZAHLUNG_AB_A12 if nummer >= 12 else SONDERZAHLUNG_BIS_A11


def _alter_am(stichtag, geburtsdatum):
    return (
        stichtag.year
        - geburtsdatum.year
        - ((stichtag.month, stichtag.day) < (geburtsdatum.month, geburtsdatum.day))
    )


def _beihilfe_jahr(jahr):
    """Jüngstes Beitragsjahr <= jahr; sonst das älteste vorhandene."""
    jahre = list(
        Beihilfesatz.objects.values_list("jahr", flat=True).distinct().order_by("-jahr")
    )
    if not jahre:
        return None
    for kandidat in jahre:
        if kandidat <= jahr:
            return kandidat
    return jahre[-1]


def _ofz_kinder_basis(zeile, kinder):
    """Monatsbetrag der „Kind n“-Spalte (inkl. Verheirateten-Anteil)."""
    if kinder == 1:
        return zeile.stufe_1
    basis = zeile.stufe_2
    if basis is None:
        return None
    if kinder >= 3 and zeile.kind_3 is not None:
        basis += zeile.kind_3
    if kinder > 3 and zeile.kind_weitere is not None:
        basis += zeile.kind_weitere * (kinder - 3)
    return basis


def hochrechnung_berechnen(einsatz, jahr):
    """Monatsmatrix + Jahressummen für einen Einsatz.

    Rückgabe: dict mit "eingaben", "monate" (Liste), "summen" (dict).
    Wirft KalkulationsFehler mit allen fehlenden Angaben auf einmal.
    """
    mitarbeiter = einsatz.mitarbeiter
    fehler = []

    gruppe = mitarbeiter.status_besoldung
    stufe = mitarbeiter.status_stufe
    umfang = Decimal(einsatz.umfang)
    kinder = mitarbeiter.kinder or 0
    verheiratet = mitarbeiter.familienstand in (
        mitarbeiter.Familienstand.VERHEIRATET,
        mitarbeiter.Familienstand.PARTNERSCHAFT,
    )

    if not mitarbeiter.ortsklasse:
        fehler.append("Ortsklasse fehlt am Mitarbeiter (Wohnort → Mietenstufe).")
    if mitarbeiter.beihilfe_art == mitarbeiter.BeihilfeArt.GESETZLICH and (
        mitarbeiter.kv_zuschuss_monat is None and mitarbeiter.beihilfe_monat is None
    ):
        fehler.append("Freiwillig gesetzlich versichert, aber KV-Zuschuss/Beihilfeanspruch fehlen.")

    einrichtung = einsatz.stelle.einrichtung
    versorgungssatz = Decimal(einrichtung.versorgungsumlage)

    beihilfe_jahr = _beihilfe_jahr(jahr)
    if beihilfe_jahr is None and mitarbeiter.beihilfe_art in (
        mitarbeiter.BeihilfeArt.PRIVAT_ALTER,
        mitarbeiter.BeihilfeArt.PRIVAT_PAUSCHAL,
    ):
        fehler.append("Keine Beihilfesätze in der Datenbank (Import/Admin).")

    if fehler:
        raise KalkulationsFehler(fehler)

    monate = []
    summe = {
        "grundbezug": Decimal("0"), "ofz": Decimal("0"), "ofz_kinder": Decimal("0"),
        "strukturzulage": Decimal("0"), "sonderzahlung": Decimal("0"),
        "beihilfe": Decimal("0"), "kv_zuschuss": Decimal("0"), "umlage": Decimal("0"),
    }

    for monat in range(1, 13):
        stichtag = date(jahr, monat, 1)

        besoldungstabelle = Besoldungstabelle.gueltig_fuer(stichtag)
        if besoldungstabelle is None:
            fehler.append(f"Keine Besoldungstabelle gültig für {stichtag:%m/%Y}.")
            break
        try:
            grundbetrag = besoldungstabelle.betraege.get(gruppe=gruppe, stufe=stufe).betrag
        except Besoldungsbetrag.DoesNotExist:
            fehler.append(
                f"Kein Besoldungsbetrag für {gruppe} Stufe {stufe} in Tabelle ab "
                f"{besoldungstabelle.gueltig_ab:%d.%m.%Y}."
            )
            break
        grundbezug = grundbetrag * umfang

        fz_tabelle = Familienzuschlagtabelle.gueltig_fuer(stichtag)
        if fz_tabelle is None:
            fehler.append(f"Keine OFZ-Tabelle gültig für {stichtag:%m/%Y}.")
            break
        try:
            fz_zeile = fz_tabelle.zeilen.get(ortsklasse=mitarbeiter.ortsklasse)
        except fz_tabelle.zeilen.model.DoesNotExist:
            fehler.append(
                f"OFZ-Tabelle ab {fz_tabelle.gueltig_ab:%d.%m.%Y} hat keine "
                f"Ortsklasse {mitarbeiter.ortsklasse}."
            )
            break

        ofz = Decimal("0")
        ofz_kinder = Decimal("0")
        if kinder == 0:
            basis = fz_zeile.stufe_v if verheiratet else fz_zeile.stufe_l
            ofz = (basis or Decimal("0")) * umfang
        else:
            basis = _ofz_kinder_basis(fz_zeile, kinder)
            if basis is None:
                fehler.append(
                    f"OFZ-Tabelle ab {fz_tabelle.gueltig_ab:%d.%m.%Y}: kein Betrag für "
                    f"{kinder} Kind(er) in Ortsklasse {mitarbeiter.ortsklasse}."
                )
                break
            ofz_kinder = basis * umfang

        strukturzulage = Decimal("0")
        if gruppe in STRUKTURZULAGE_GRUPPEN:
            satz = Zulagensatz.gueltig_fuer(Zulagensatz.Art.STRUKTUR, stichtag)
            if satz is None:
                fehler.append(f"Kein Strukturzulagensatz gültig für {stichtag:%m/%Y}.")
                break
            strukturzulage = satz.betrag * umfang

        beihilfe = Decimal("0")
        kv_zuschuss = Decimal("0")
        art = mitarbeiter.BeihilfeArt
        if mitarbeiter.beihilfe_art in (art.PRIVAT_ALTER, art.PRIVAT_PAUSCHAL):
            tarif = "830" if mitarbeiter.beihilfe_art == art.PRIVAT_ALTER else "814"
            alter = _alter_am(stichtag, mitarbeiter.geburtsdatum)
            satz = Beihilfesatz.satz_fuer(beihilfe_jahr, tarif, alter)
            if satz is None:
                fehler.append(f"Kein Beihilfesatz (Tarif {tarif}, Alter {alter}, Jahr {beihilfe_jahr}).")
                break
            beihilfe = satz
            if tarif == "830":
                if mitarbeiter.ehegatte_beihilfe:
                    beihilfe += satz
                if kinder:
                    kindersatz = Beihilfesatz.kindersatz_fuer(beihilfe_jahr, tarif) or Decimal("0")
                    beihilfe += kindersatz * kinder
            beihilfe *= umfang
        elif mitarbeiter.beihilfe_art == art.GESETZLICH:
            beihilfe = (
                (mitarbeiter.beihilfe_monat or Decimal("0"))
                + (mitarbeiter.beihilfe_kinder_monat or Decimal("0"))
            ) * umfang
            kv_zuschuss = (mitarbeiter.kv_zuschuss_monat or Decimal("0")) * umfang

        monate.append(
            {
                "monat": monat,
                "name": MONATSNAMEN[monat - 1],
                "grundbezug": grundbezug,
                "ofz": ofz,
                "ofz_kinder": ofz_kinder,
                "strukturzulage": strukturzulage,
                "sonderzahlung": Decimal("0"),
                "beihilfe": beihilfe,
                "kv_zuschuss": kv_zuschuss,
            }
        )
        for feld in ("grundbezug", "ofz", "ofz_kinder", "strukturzulage", "beihilfe", "kv_zuschuss"):
            summe[feld] += monate[-1][feld]

    if fehler:
        raise KalkulationsFehler(fehler)

    # Jährliche Sonderzahlung im Dezember (Jahressumme der Bezüge / 12 × Faktor)
    bezuege_summe = summe["grundbezug"] + summe["ofz"] + summe["ofz_kinder"] + summe["strukturzulage"]
    sonderzahlung = bezuege_summe / 12 * _sonderzahlung_faktor(gruppe)
    monate[11]["sonderzahlung"] = sonderzahlung
    summe["sonderzahlung"] = sonderzahlung

    # Versorgungsumlage je Monat auf Bezüge inkl. Sonderzahlung
    for zeile in monate:
        zeile["umlage"] = (
            zeile["grundbezug"] + zeile["ofz"] + zeile["ofz_kinder"]
            + zeile["strukturzulage"] + zeile["sonderzahlung"]
        ) * versorgungssatz
        summe["umlage"] += zeile["umlage"]

    grundbezuege_gesamt = bezuege_summe + sonderzahlung
    gesamt = grundbezuege_gesamt + summe["beihilfe"] + summe["kv_zuschuss"] + summe["umlage"]

    def q(wert):
        return wert.quantize(ZWEI_STELLEN, rounding=ROUND_HALF_UP)

    return {
        "eingaben": {
            "jahr": jahr,
            "besoldungsgruppe": gruppe,
            "stufe": stufe,
            "umfang": str(umfang),
            "ortsklasse": mitarbeiter.ortsklasse,
            "familienstand": mitarbeiter.get_familienstand_display(),
            "kinder": kinder,
            "beihilfe_art": mitarbeiter.get_beihilfe_art_display(),
            "ehegatte_beihilfe": mitarbeiter.ehegatte_beihilfe,
            "beihilfe_beitragsjahr": beihilfe_jahr,
            "versorgungsumlage_satz": str(versorgungssatz),
            "sonderzahlung_faktor": str(_sonderzahlung_faktor(gruppe)),
        },
        "monate": [
            {schluessel: (str(q(wert)) if isinstance(wert, Decimal) else wert) for schluessel, wert in zeile.items()}
            for zeile in monate
        ],
        "summen": {
            "grundbezug": q(summe["grundbezug"]),
            "ofz": q(summe["ofz"]),
            "ofz_kinder": q(summe["ofz_kinder"]),
            "strukturzulage": q(summe["strukturzulage"]),
            "sonderzahlung": q(sonderzahlung),
            "grundbezuege_gesamt": q(grundbezuege_gesamt),
            "beihilfe": q(summe["beihilfe"]),
            "kv_zuschuss": q(summe["kv_zuschuss"]),
            "umlage": q(summe["umlage"]),
            "gesamt": q(gesamt),
        },
    }


def abschlag_vorschlag(gesamt):
    """Quartalsabschlag: Jahres-Hochrechnung / 4, abgerundet auf volle 500 €."""
    viertel = Decimal(gesamt) / 4
    return (viertel / 500).to_integral_value(rounding="ROUND_FLOOR") * 500
