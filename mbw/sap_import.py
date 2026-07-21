"""SAP-Personalkosten-Auswertung („Dynamische Listenausgabe“) einlesen.

Dateiformat: UTF-16, tabgetrennt, CRLF; einige Titelzeilen, dann die
Kopfzeile (erkennbar an „PersNr“), dann Buchungszeilen. Beträge mit
deutschem Komma, Rückrechnungen erscheinen als +/−-Paare gleicher
Lohnart und Für-Periode („Stornos“), die sich gegenseitig aufheben.
"""

from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation

from django.db import transaction

from personal.models import Mitarbeiter

from .models import Innenauftrag, PersonalkostenImport, PersonalkostenZeile

# Kopfzeilen-Beschriftung -> Modellfeld
SPALTEN = {
    "PersNr": "personalnummer",
    "Nachname": "nachname",
    "Vorname": "vorname",
    "L B E": "lbe",
    "Kostenst.": "kostenstelle",
    "Auftrag": "auftrag_nummer",
    "Hauptb": "hauptbuchkonto",
    "LArt": "lohnart",
    "Lohnart-Langtext": "lohnart_text",
    "Betrag": "betrag",
    "Währg": "waehrung",
    "Text": "text",
    "Fürper.": "fuer_periode",
    "Inper.": "in_periode",
}


class SapImportFehler(Exception):
    pass


def _betrag(wert):
    wert = wert.replace(".", "").replace(",", ".").strip()
    try:
        return Decimal(wert)
    except InvalidOperation:
        raise SapImportFehler(f"Betrag nicht lesbar: {wert!r}")


def _dekodieren(rohdaten):
    if isinstance(rohdaten, str):
        return rohdaten
    for kodierung in ("utf-16", "utf-8-sig", "cp1252"):
        try:
            return rohdaten.decode(kodierung)
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise SapImportFehler("Datei-Kodierung nicht erkannt (erwartet UTF-16 aus SAP).")


def sap_datei_parsen(rohdaten):
    """Rohdaten -> Liste von Zeilen-Dicts (Modellfelder, ohne Import-Bezug)."""
    text = _dekodieren(rohdaten)
    zeilen = []
    spalten_index = None

    for roh_zeile in text.splitlines():
        felder = [feld.strip() for feld in roh_zeile.split("\t")]
        if spalten_index is None:
            if "PersNr" in felder:
                spalten_index = {
                    feldname: felder.index(beschriftung)
                    for beschriftung, feldname in SPALTEN.items()
                    if beschriftung in felder
                }
                fehlend = set(SPALTEN.values()) - set(spalten_index)
                if fehlend:
                    raise SapImportFehler(
                        f"Kopfzeile unvollständig, fehlende Spalten: {', '.join(sorted(fehlend))}"
                    )
            continue

        persnr = felder[spalten_index["personalnummer"]] if len(felder) > spalten_index["personalnummer"] else ""
        if not persnr.isdigit():
            continue

        daten = {}
        for feldname, index in spalten_index.items():
            wert = felder[index] if index < len(felder) else ""
            daten[feldname] = _betrag(wert) if feldname == "betrag" else wert
        zeilen.append(daten)

    if spalten_index is None:
        raise SapImportFehler("Keine Kopfzeile mit „PersNr“ gefunden – ist das die SAP-Listenausgabe?")
    if not zeilen:
        raise SapImportFehler("Keine Buchungszeilen in der Datei gefunden.")
    return zeilen


# RV-Gegenbuchungen: Arbeitgeber-Aufstockung (+) und deren Übernahme (−) laufen
# über zwei verschiedene Lohnarten und heben sich je Für-Periode auf. Schlüssel
# ist die jeweils andere Lohnart des Paars.
RV_GEGENPAARE = {
    "1S32": "9V98", "9V98": "1S32",
    "/361": "9V61", "9V61": "/361",
    "/363": "9V63", "9V63": "/363",
}


def _stornos_markieren(zeilen):
    """Markiert sich aufhebende +X/−X-Buchungen als Storno-Paare.

    Zwei Arten von Nullpaaren werden erkannt:
      1. Rückrechnungen – gleiche Lohnart/Für-Periode/Konto, +X und −X, egal in
         welcher Reihenfolge sie in der Datei stehen. SAP bucht die Stornierung
         oft VOR der Neubuchung einer späteren In-Periode; das frühere Verfahren
         paarte nur mit einem bereits gesehenen Plus und übersah diese Fälle.
      2. RV-Gegenbuchungen – Aufstockung und Übernahme über zwei verschiedene
         Lohnarten (siehe RV_GEGENPAARE), die sich je Für-Periode aufheben.

    zeilen: Liste von Dicts in Dateireihenfolge; ergänzt je Zeile den Schlüssel
    "storno_index" (Index des Partners) oder None. Rückgabe: Anzahl Paare.
    """
    for zeile in zeilen:
        zeile["storno_index"] = None

    def paaren(schluessel_fn):
        """Paart offene +X mit offenen −X je Gruppe. `schluessel_fn` liefert den
        Gruppen-Schlüssel (oder None, um die Zeile zu überspringen)."""
        positive = defaultdict(list)  # (Gruppe, |Betrag|) -> [Index, ...]
        negative = defaultdict(list)
        for index, zeile in enumerate(zeilen):
            if zeile["storno_index"] is not None:
                continue
            gruppe = schluessel_fn(zeile)
            if gruppe is None:
                continue
            betrag = zeile["betrag"]
            ziel = positive if betrag >= 0 else negative
            ziel[(gruppe, abs(betrag))].append(index)

        anzahl = 0
        for schluessel, pos_indizes in positive.items():
            for pos_index, neg_index in zip(pos_indizes, negative.get(schluessel, [])):
                zeilen[pos_index]["storno_index"] = neg_index
                zeilen[neg_index]["storno_index"] = pos_index
                anzahl += 1
        return anzahl

    def gleiche_lohnart(zeile):
        return (
            zeile["personalnummer"], zeile["auftrag_nummer"],
            zeile["hauptbuchkonto"], zeile["lohnart"], zeile["fuer_periode"],
        )

    def rv_gegenpaar(zeile):
        partner = RV_GEGENPAARE.get(zeile["lohnart"])
        if partner is None:
            return None
        # Beide Lohnarten sortiert -> beide Seiten landen in derselben Gruppe.
        lohnart_paar = tuple(sorted((zeile["lohnart"], partner)))
        return (
            zeile["personalnummer"], zeile["auftrag_nummer"],
            zeile["hauptbuchkonto"], lohnart_paar, zeile["fuer_periode"],
        )

    # Erst die einfachen Rückrechnungen, dann die verbleibenden RV-Gegenbuchungen.
    return paaren(gleiche_lohnart) + paaren(rv_gegenpaar)


@transaction.atomic
def sap_import_anlegen(rohdaten, dateiname, benutzer=None, bemerkung=""):
    """Parst die Datei und legt Import + Zeilen inkl. Storno-Paaren an."""
    zeilen = sap_datei_parsen(rohdaten)
    paare = _stornos_markieren(zeilen)

    jahre = Counter(
        zeile["fuer_periode"][:4] for zeile in zeilen if len(zeile["fuer_periode"]) >= 4
    )
    jahr = int(jahre.most_common(1)[0][0]) if jahre else 0

    import_lauf = PersonalkostenImport.objects.create(
        dateiname=dateiname, jahr=jahr, bemerkung=bemerkung, hochgeladen_von=benutzer
    )

    auftraege = {ia.nummer: ia for ia in Innenauftrag.objects.all()}
    personalnummern = set(Mitarbeiter.objects.values_list("personalnummer", flat=True))

    objekte = []
    for index, zeile in enumerate(zeilen, start=1):
        felder = {name: wert for name, wert in zeile.items() if name != "storno_index"}
        objekte.append(
            PersonalkostenZeile(
                import_lauf=import_lauf,
                lfd_nr=index,
                innenauftrag=auftraege.get(zeile["auftrag_nummer"]),
                mitarbeiter_id=zeile["personalnummer"] if zeile["personalnummer"] in personalnummern else None,
                **felder,
            )
        )
    PersonalkostenZeile.objects.bulk_create(objekte)

    partner_updates = []
    for index, zeile in enumerate(zeilen):
        if zeile["storno_index"] is not None:
            objekte[index].storno_partner = objekte[zeile["storno_index"]]
            partner_updates.append(objekte[index])
    PersonalkostenZeile.objects.bulk_update(partner_updates, ["storno_partner"])

    return import_lauf, {"zeilen": len(objekte), "storno_paare": paare}


def faelle(import_lauf):
    """Fälle (Person × Innenauftrag) mit Summen je Hauptbuchkonto.

    Rückgabe: Liste von Dicts, sortiert nach Nachname/Vorname.
    """
    ergebnis = {}
    zeilen = import_lauf.zeilen.select_related(
        "innenauftrag", "innenauftrag__debitor", "innenauftrag__einsatz", "mitarbeiter"
    )
    for zeile in zeilen:
        schluessel = (zeile.personalnummer, zeile.auftrag_nummer)
        fall = ergebnis.get(schluessel)
        if fall is None:
            fall = ergebnis[schluessel] = {
                "personalnummer": zeile.personalnummer,
                "nachname": zeile.nachname,
                "vorname": zeile.vorname,
                "auftrag_nummer": zeile.auftrag_nummer,
                "kostenstelle": zeile.kostenstelle,
                "innenauftrag": zeile.innenauftrag,
                "mitarbeiter": zeile.mitarbeiter,
                "zeilen_anzahl": 0,
                "konten": defaultdict(lambda: Decimal("0")),
            }
        fall["zeilen_anzahl"] += 1
        # Storno-Paare heben sich auf – nur sichtbare Zeilen fließen in die Summen.
        if zeile.storno_partner_id is None:
            fall["konten"][zeile.hauptbuchkonto] += zeile.betrag

    for fall in ergebnis.values():
        fall["konten"] = dict(fall["konten"])
        fall["bezuege"] = fall["konten"].get("603100", Decimal("0"))
        fall["umlage"] = fall["konten"].get("609800", Decimal("0"))
        fall["gesamt"] = sum(fall["konten"].values(), Decimal("0"))
        fall["einsatz"] = fall["innenauftrag"].einsatz if fall["innenauftrag"] else None
        fall["debitor"] = fall["innenauftrag"].debitor if fall["innenauftrag"] else None

    return sorted(ergebnis.values(), key=lambda fall: (fall["nachname"], fall["vorname"], fall["auftrag_nummer"]))


def fall_zeilen(import_lauf, personalnummer, auftrag_nummer):
    """Zeilen eines Falls, gruppiert nach Lohnart (Reihenfolge des Auftretens)."""
    zeilen = list(
        import_lauf.zeilen.filter(
            personalnummer=personalnummer, auftrag_nummer=auftrag_nummer
        ).select_related("storno_partner").order_by("lfd_nr")
    )
    gruppen = []
    index = {}
    for zeile in zeilen:
        schluessel = (zeile.lohnart, zeile.lohnart_text)
        if schluessel not in index:
            index[schluessel] = len(gruppen)
            gruppen.append({"lohnart": zeile.lohnart, "lohnart_text": zeile.lohnart_text, "zeilen": [], "summe": Decimal("0")})
        gruppe = gruppen[index[schluessel]]
        gruppe["zeilen"].append(zeile)
        # Storno-Zeilen bleiben sichtbar (grau markiert), zählen aber nicht zur Summe.
        if zeile.storno_partner_id is None:
            gruppe["summe"] += zeile.betrag
    return gruppen
