"""import_export-Resources für die MBW-Stammdaten (Debitoren, Innenaufträge).

Teilnahme am datenaustausch-Gesamtexport/-import (siehe datenaustausch/registry.py).
Roundtrip-fähig: eine exportierte Mappe lässt sich unverändert wieder importieren.

- Debitor hat keinen fachlichen Schlüssel (die SAP-Debitorennummer ist teils
  leer oder mehrdeutig), daher ist der Schlüssel die interne Id. Leere Id-Zelle
  = neuer Debitor.
- Innenauftrag wird über seine eindeutige Nummer geschlüsselt; der Debitor-Bezug
  läuft über dessen interne Id. Der Einsatz-Bezug wird nur zur Info exportiert
  (read-only) und beim Import nicht verändert.
"""

from django.core.exceptions import ValidationError
from import_export import fields, resources, widgets

from datenaustausch.widgets import (
    ChoiceLabelWidget,
    GanzzahlWidget,
    JaNeinWidget,
    TextWidget,
    _text,
)
from traeger.models import Traeger

from .models import Debitor, Innenauftrag


class TraegerIdOptionalWidget(widgets.ForeignKeyWidget):
    """Träger-Verweis über die (eindeutige) Träger-Id – leer ist erlaubt."""

    def __init__(self, model):
        super().__init__(model, field="traeger_id")

    def clean(self, value, row=None, **kwargs):
        tid = _text(value)
        if not tid:
            return None
        try:
            return self.model.objects.get(traeger_id=tid)
        except self.model.DoesNotExist:
            raise ValueError(
                f"Kein Träger mit Träger-Id '{tid}' gefunden – "
                "bitte zuerst im Blatt 'Träger' anlegen."
            )
        except self.model.MultipleObjectsReturned:
            raise ValueError(f"Träger-Id '{tid}' ist mehrfach vergeben – bitte in der App bereinigen.")

    def render(self, value, obj=None, **kwargs):
        return value.traeger_id if value else ""


class DebitorIdWidget(widgets.ForeignKeyWidget):
    """Debitor-Verweis über die interne Id (aus Spalte 'Id' des Debitoren-Blatts).
    Leer ist erlaubt (Innenauftrag ohne Debitor)."""

    def __init__(self):
        super().__init__(Debitor, field="pk")

    def clean(self, value, row=None, **kwargs):
        kennung = _text(value)
        if not kennung:
            return None
        try:
            return Debitor.objects.get(pk=int(kennung))
        except (ValueError, Debitor.DoesNotExist):
            raise ValueError(
                f"Kein Debitor mit Id '{kennung}' gefunden – "
                "bitte zuerst im Blatt 'Debitoren' anlegen (Spalte 'Id')."
            )

    def render(self, value, obj=None, **kwargs):
        return value.pk if value else ""


class DebitorResource(resources.ModelResource):
    """Blatt 'Debitoren'. Schlüssel: interne Id (leer = neuer Debitor)."""

    id = fields.Field(column_name="Id", attribute="id", widget=GanzzahlWidget())
    sap_nummer = fields.Field(column_name="SAP-Debitorennummer", attribute="sap_nummer", widget=TextWidget())
    name = fields.Field(column_name="Name", attribute="name", widget=TextWidget())
    name2 = fields.Field(column_name="Namenszusatz", attribute="name2", widget=TextWidget())
    anschriftperson = fields.Field(column_name="Anschriftperson", attribute="anschriftperson", widget=TextWidget())
    strasse = fields.Field(column_name="Straße", attribute="strasse", widget=TextWidget())
    plz = fields.Field(column_name="PLZ", attribute="plz", widget=TextWidget())
    ort = fields.Field(column_name="Ort", attribute="ort", widget=TextWidget())
    email = fields.Field(column_name="E-Mail", attribute="email", widget=TextWidget())
    versandweg = fields.Field(
        column_name="Versandweg",
        attribute="versandweg",
        widget=ChoiceLabelWidget(Debitor.Versandweg.choices),
    )
    traeger = fields.Field(
        column_name="Träger-Id",
        attribute="traeger",
        widget=TraegerIdOptionalWidget(Traeger),
    )
    aktiv = fields.Field(column_name="Aktiv", attribute="aktiv", widget=JaNeinWidget(default=True))
    bemerkung = fields.Field(column_name="Bemerkung", attribute="bemerkung", widget=TextWidget())

    class Meta:
        model = Debitor
        import_id_fields = ("id",)
        fields = (
            "id",
            "sap_nummer",
            "name",
            "name2",
            "anschriftperson",
            "strasse",
            "plz",
            "ort",
            "email",
            "versandweg",
            "traeger",
            "aktiv",
            "bemerkung",
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True

    def before_import_row(self, row, **kwargs):
        if not _text(row.get("Name")):
            raise ValidationError("Name darf nicht leer sein.")


class InnenauftragResource(resources.ModelResource):
    """Blatt 'Innenaufträge'. Schlüssel: Innenauftrag-Nummer (eindeutig).

    Der Einsatz-Bezug (Person/Stelle) wird nur zur Orientierung exportiert und
    beim Import nicht verändert – die Zuordnung erfolgt weiterhin in der App.
    """

    nummer = fields.Field(column_name="Innenauftrag", attribute="nummer", widget=TextWidget())
    bezeichnung = fields.Field(column_name="Bezeichnung", attribute="bezeichnung", widget=TextWidget())
    kostenstelle = fields.Field(column_name="Kostenstelle", attribute="kostenstelle", widget=TextWidget())
    debitor = fields.Field(column_name="Debitor-Id", attribute="debitor", widget=DebitorIdWidget())
    aktiv = fields.Field(column_name="Aktiv", attribute="aktiv", widget=JaNeinWidget(default=True))
    bemerkung = fields.Field(column_name="Bemerkung", attribute="bemerkung", widget=TextWidget())
    # Nur-Info-Spalten (read-only): zeigen den in der App gepflegten Einsatz-Bezug.
    andock_art = fields.Field(
        column_name="Andock-Art",
        attribute="andock_art",
        widget=ChoiceLabelWidget(Innenauftrag.AndockArt.choices),
        readonly=True,
    )
    einsatz_person = fields.Field(
        column_name="Einsatz (Personalnr.)",
        attribute="einsatz__mitarbeiter__personalnummer",
        readonly=True,
    )
    einsatz_stelle = fields.Field(
        column_name="Einsatz (Stellen-Id)",
        attribute="einsatz__stelle__stellen_id",
        readonly=True,
    )

    class Meta:
        model = Innenauftrag
        import_id_fields = ("nummer",)
        fields = (
            "nummer",
            "bezeichnung",
            "kostenstelle",
            "debitor",
            "aktiv",
            "bemerkung",
            "andock_art",
            "einsatz_person",
            "einsatz_stelle",
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True

    def before_import_row(self, row, **kwargs):
        if not _text(row.get("Innenauftrag")):
            raise ValidationError("Innenauftrag-Nummer darf nicht leer sein.")
