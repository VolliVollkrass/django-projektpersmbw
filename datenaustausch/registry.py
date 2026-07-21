"""Zentrale Konfiguration: welche Blätter/Modelle am Import/Export teilnehmen.

Die Reihenfolge ist die Import-Reihenfolge (spätere Blätter verweisen auf
frühere). Sheetnamen und Spalten entsprechen der Datei
import_vorlagen/Stammdaten-Import-Vorlage.xlsx.
"""

from dataclasses import dataclass

from django.db.models import Q

from ansprechpartner.models import Ansprechpartner
from ansprechpartner.resources import AnsprechpartnerResource
from einsatz.models import Einsatz
from einsatz.resources import EinsatzResource
from mbw.models import Debitor, Innenauftrag
from mbw.resources import DebitorResource, InnenauftragResource
from personal.models import Mitarbeiter
from personal.resources import MitarbeiterResource
from traeger.models import Einrichtung, Stelle, Traeger
from traeger.resources import EinrichtungResource, StelleResource, TraegerResource


@dataclass(frozen=True)
class SheetConfig:
    sheet_name: str          # Blattname in der Excel-Mappe
    slug: str                # URL-Kürzel für Einzel-Exporte
    resource_class: type
    model: type
    pflicht_spalten: tuple   # für die Markerzeile beim Export
    such_filter: object = None  # Q-Filter-Fabrik für den Listen-Export (?q=…)


def _q_traeger(q):
    return Q(name__icontains=q) | Q(traeger_id__icontains=q) | Q(art__icontains=q)


def _q_einrichtung(q):
    return Q(name__icontains=q) | Q(einrichtungs_id__icontains=q) | Q(einrichtung_art__icontains=q)


def _q_stelle(q):
    return Q(name__icontains=q) | Q(stellen_id__icontains=q) | Q(plz__icontains=q) | Q(ort__icontains=q)


def _q_mitarbeiter(q):
    return Q(personalnummer__icontains=q) | Q(vorname__icontains=q) | Q(nachname__icontains=q)


def _q_ansprechpartner(q):
    return Q(email__icontains=q) | Q(vorname__icontains=q) | Q(nachname__icontains=q)


def _q_einsatz(q):
    return (
        Q(stelle__name__icontains=q)
        | Q(mitarbeiter__vorname__icontains=q)
        | Q(mitarbeiter__nachname__icontains=q)
    )


def _q_debitor(q):
    return Q(name__icontains=q) | Q(sap_nummer__icontains=q) | Q(ort__icontains=q)


def _q_innenauftrag(q):
    return Q(nummer__icontains=q) | Q(kostenstelle__icontains=q) | Q(bezeichnung__icontains=q)


SHEETS = [
    SheetConfig(
        sheet_name="Ansprechpartner",
        slug="ansprechpartner",
        resource_class=AnsprechpartnerResource,
        model=Ansprechpartner,
        pflicht_spalten=("Vorname", "Nachname"),
        such_filter=_q_ansprechpartner,
    ),
    SheetConfig(
        sheet_name="Träger",
        slug="traeger",
        resource_class=TraegerResource,
        model=Traeger,
        pflicht_spalten=("Träger-Id", "Name"),
        such_filter=_q_traeger,
    ),
    SheetConfig(
        sheet_name="Einrichtungen",
        slug="einrichtungen",
        resource_class=EinrichtungResource,
        model=Einrichtung,
        pflicht_spalten=("Einrichtungs-Id", "Name", "Träger-Id"),
        such_filter=_q_einrichtung,
    ),
    SheetConfig(
        sheet_name="Stellen",
        slug="stellen",
        resource_class=StelleResource,
        model=Stelle,
        pflicht_spalten=("Stellen-Id", "Name", "Einrichtungs-Id"),
        such_filter=_q_stelle,
    ),
    SheetConfig(
        sheet_name="Mitarbeiter",
        slug="mitarbeiter",
        resource_class=MitarbeiterResource,
        model=Mitarbeiter,
        pflicht_spalten=("Personalnummer", "Vorname", "Nachname", "Geburtsdatum"),
        such_filter=_q_mitarbeiter,
    ),
    SheetConfig(
        sheet_name="Einsätze",
        slug="einsaetze",
        resource_class=EinsatzResource,
        model=Einsatz,
        pflicht_spalten=("Stellen-Id", "Personalnummer", "Beginn"),
        such_filter=_q_einsatz,
    ),
    SheetConfig(
        sheet_name="Debitoren",
        slug="debitoren",
        resource_class=DebitorResource,
        model=Debitor,
        pflicht_spalten=("Name",),
        such_filter=_q_debitor,
    ),
    SheetConfig(
        sheet_name="Innenaufträge",
        slug="innenauftraege",
        resource_class=InnenauftragResource,
        model=Innenauftrag,
        pflicht_spalten=("Innenauftrag",),
        such_filter=_q_innenauftrag,
    ),
]

SHEETS_BY_SLUG = {s.slug: s for s in SHEETS}
SHEETS_BY_NAME = {s.sheet_name: s for s in SHEETS}

# Rechteprüfung: Import/Export nur für Sachbearbeitung/Administration
SCHREIB_RECHTE = (
    "ansprechpartner.change_ansprechpartner",
    "traeger.change_traeger",
    "traeger.change_einrichtung",
    "traeger.change_stelle",
    "personal.change_mitarbeiter",
    "einsatz.change_einsatz",
)
