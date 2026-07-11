"""Fachlogik für die Mittelbewirtschaftung (Stammdaten-Fortschreibung)."""

from decimal import ROUND_HALF_UP, Decimal

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
