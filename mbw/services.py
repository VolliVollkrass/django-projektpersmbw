"""Fachlogik für die Mittelbewirtschaftung (Stammdaten-Fortschreibung + direkte Pflege)."""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.db import transaction

from .models import (
    Besoldungsbetrag,
    Besoldungstabelle,
    Familienzuschlagtabelle,
    Familienzuschlagzeile,
    FZKinderErhoehung,
)


def _erhoeht(betrag, prozent):
    if betrag is None:
        return None
    faktor = Decimal("1") + prozent / Decimal("100")
    return (betrag * faktor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def betrag_parsen(rohwert):
    """Zellwert -> Decimal (deutsches Komma) oder None bei leer. Wirft ValueError."""
    text = (rohwert or "").strip().replace(".", "").replace(",", ".") if rohwert else ""
    if not text:
        return None
    try:
        return Decimal(text).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ValueError(f"„{rohwert}“ ist kein gültiger Betrag.")


def _gueltig_ab_pruefen(modell, gueltig_ab, tabelle):
    if gueltig_ab is None:
        raise ValueError("Bitte ein Gültig-ab-Datum angeben.")
    kollision = modell.objects.filter(gueltig_ab=gueltig_ab)
    if tabelle and tabelle.pk:
        kollision = kollision.exclude(pk=tabelle.pk)
    if kollision.exists():
        raise ValueError(f"Es gibt bereits eine Tabelle mit Gültig-ab {gueltig_ab:%d.%m.%Y}.")


@transaction.atomic
def besoldungstabelle_speichern(tabelle, gueltig_ab, bemerkung, betrag_map):
    """Legt eine Besoldungstabelle an oder aktualisiert sie inkl. Beträge.

    betrag_map: {(gruppe, stufe): Decimal|None}. None löscht den vorhandenen Betrag.
    """
    _gueltig_ab_pruefen(Besoldungstabelle, gueltig_ab, tabelle)
    if tabelle is None:
        tabelle = Besoldungstabelle(erhoehung_prozent=None)
    tabelle.gueltig_ab = gueltig_ab
    tabelle.bemerkung = bemerkung
    tabelle.save()

    for (gruppe, stufe), betrag in betrag_map.items():
        if betrag is None:
            Besoldungsbetrag.objects.filter(tabelle=tabelle, gruppe=gruppe, stufe=stufe).delete()
        else:
            Besoldungsbetrag.objects.update_or_create(
                tabelle=tabelle, gruppe=gruppe, stufe=stufe, defaults={"betrag": betrag}
            )
    return tabelle


@transaction.atomic
def fz_tabelle_speichern(tabelle, gueltig_ab, bemerkung, zeilen_map, kinder_map):
    """Legt eine OFZ-Tabelle an oder aktualisiert sie inkl. Zeilen und Kindererhöhungen.

    zeilen_map: {ortsklasse: {feld: Decimal|None}} (Felder: stufe_l/stufe_v/stufe_1/
                stufe_2/kind_3/kind_weitere).
    kinder_map: {(gruppe, ortsklasse): Decimal|None}.
    """
    _gueltig_ab_pruefen(Familienzuschlagtabelle, gueltig_ab, tabelle)
    if tabelle is None:
        tabelle = Familienzuschlagtabelle(erhoehung_prozent=None)
    tabelle.gueltig_ab = gueltig_ab
    tabelle.bemerkung = bemerkung
    tabelle.save()

    for ortsklasse, felder in zeilen_map.items():
        if all(wert is None for wert in felder.values()):
            Familienzuschlagzeile.objects.filter(tabelle=tabelle, ortsklasse=ortsklasse).delete()
        else:
            Familienzuschlagzeile.objects.update_or_create(
                tabelle=tabelle, ortsklasse=ortsklasse, defaults=felder
            )

    for (gruppe, ortsklasse), betrag in kinder_map.items():
        if betrag is None:
            FZKinderErhoehung.objects.filter(
                tabelle=tabelle, gruppe=gruppe, ortsklasse=ortsklasse
            ).delete()
        else:
            FZKinderErhoehung.objects.update_or_create(
                tabelle=tabelle, gruppe=gruppe, ortsklasse=ortsklasse, defaults={"betrag": betrag}
            )
    return tabelle


@transaction.atomic
def besoldungstabelle_fortschreiben(gueltig_ab, prozent):
    """Neue Besoldungstabelle = jüngste Tabelle × (1 + Prozent), wie in der
    Excel-Vorlage (ROUND(alt × Faktor, 2))."""
    basis = Besoldungstabelle.objects.order_by("-gueltig_ab").first()
    if basis is None:
        raise ValueError("Keine Basistabelle vorhanden – zuerst importieren.")
    if basis.gueltig_ab >= gueltig_ab:
        raise ValueError(
            f"Gültig-ab muss nach der jüngsten Tabelle ({basis.gueltig_ab:%d.%m.%Y}) liegen."
        )

    tabelle = Besoldungstabelle.objects.create(
        gueltig_ab=gueltig_ab,
        erhoehung_prozent=prozent,
        bemerkung=f"Fortschreibung aus Tabelle ab {basis.gueltig_ab:%d.%m.%Y} (+{prozent} %)",
    )
    Besoldungsbetrag.objects.bulk_create(
        [
            Besoldungsbetrag(
                tabelle=tabelle,
                gruppe=betrag.gruppe,
                stufe=betrag.stufe,
                betrag=_erhoeht(betrag.betrag, prozent),
            )
            for betrag in basis.betraege.all()
        ]
    )
    return tabelle


@transaction.atomic
def fz_tabelle_fortschreiben(gueltig_ab, prozent):
    """Neue OFZ-Tabelle = jüngste Tabelle × (1 + Prozent)."""
    basis = Familienzuschlagtabelle.objects.order_by("-gueltig_ab").first()
    if basis is None:
        raise ValueError("Keine Basistabelle vorhanden – zuerst importieren.")
    if basis.gueltig_ab >= gueltig_ab:
        raise ValueError(
            f"Gültig-ab muss nach der jüngsten Tabelle ({basis.gueltig_ab:%d.%m.%Y}) liegen."
        )

    tabelle = Familienzuschlagtabelle.objects.create(
        gueltig_ab=gueltig_ab,
        erhoehung_prozent=prozent,
        bemerkung=f"Fortschreibung aus Tabelle ab {basis.gueltig_ab:%d.%m.%Y} (+{prozent} %)",
    )
    Familienzuschlagzeile.objects.bulk_create(
        [
            Familienzuschlagzeile(
                tabelle=tabelle,
                ortsklasse=zeile.ortsklasse,
                stufe_l=_erhoeht(zeile.stufe_l, prozent),
                stufe_v=_erhoeht(zeile.stufe_v, prozent),
                stufe_1=_erhoeht(zeile.stufe_1, prozent),
                stufe_2=_erhoeht(zeile.stufe_2, prozent),
                kind_3=_erhoeht(zeile.kind_3, prozent),
                kind_weitere=_erhoeht(zeile.kind_weitere, prozent),
            )
            for zeile in basis.zeilen.all()
        ]
    )
    FZKinderErhoehung.objects.bulk_create(
        [
            FZKinderErhoehung(
                tabelle=tabelle,
                ortsklasse=erhoehung.ortsklasse,
                gruppe=erhoehung.gruppe,
                betrag=_erhoeht(erhoehung.betrag, prozent),
            )
            for erhoehung in basis.kinder_erhoehungen.all()
        ]
    )
    return tabelle
