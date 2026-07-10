from decimal import Decimal

from django.core.exceptions import ValidationError
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget

from datenaustausch.widgets import (
    DeutschesDatumWidget,
    JaNeinWidget,
    ProzentAnteilWidget,
    SammelIdWidget,
    TextWidget,
    _text,
)
from personal.models import Mitarbeiter
from traeger.models import Stelle
from .models import Einsatz


class PersonalnummerWidget(ForeignKeyWidget):
    def __init__(self):
        super().__init__(Mitarbeiter, field="personalnummer")

    def clean(self, value, row=None, **kwargs):
        nummer = _text(value)
        if not nummer:
            raise ValueError("Personalnummer fehlt.")
        try:
            return Mitarbeiter.objects.get(personalnummer=nummer)
        except Mitarbeiter.DoesNotExist:
            raise ValueError(
                f"Kein Mitarbeiter mit Personalnummer '{nummer}' gefunden – "
                "bitte zuerst im Blatt 'Mitarbeiter' anlegen."
            )

    def render(self, value, obj=None, **kwargs):
        return value.personalnummer if value else ""


def _stellen_widget():
    return SammelIdWidget(
        Stelle,
        id_feld="stellen_id",
        id_spalte="Stellen-Id",
        name_spalte="Stelle (Name)",
        blatt_hinweis="Stellen",
    )


class EinsatzResource(resources.ModelResource):
    """Spalten = Blatt 'Einsätze' der Vorlage.

    Fachlicher Schlüssel: Stellen-Id + Personalnummer + Beginn (ein Einsatz hat
    keine eigene Kennung). Bei Sammel-Stellen-Ids entscheidet 'Stelle (Name)'.
    """

    stelle = fields.Field(
        column_name="Stellen-Id",
        attribute="stelle",
        widget=_stellen_widget(),
    )
    stelle_name = fields.Field(
        column_name="Stelle (Name)",
        attribute="stelle__name",
        readonly=True,
    )
    mitarbeiter = fields.Field(
        column_name="Personalnummer",
        attribute="mitarbeiter",
        widget=PersonalnummerWidget(),
    )
    beginn = fields.Field(column_name="Beginn", attribute="beginn", widget=DeutschesDatumWidget())
    ende = fields.Field(column_name="Ende", attribute="ende", widget=DeutschesDatumWidget())
    umfang = fields.Field(
        column_name="Umfang", attribute="umfang", widget=ProzentAnteilWidget(default=Decimal("1.00"))
    )
    abrechnung = fields.Field(
        column_name="Abrechnung über LKA", attribute="abrechnung", widget=JaNeinWidget(default=False)
    )
    aktiv = fields.Field(column_name="Aktiv", attribute="aktiv", widget=JaNeinWidget(default=True))
    bemerkung = fields.Field(column_name="Bemerkung", attribute="bemerkung", widget=TextWidget())

    class Meta:
        model = Einsatz
        import_id_fields = ()
        fields = (
            "stelle",
            "stelle_name",
            "mitarbeiter",
            "beginn",
            "ende",
            "umfang",
            "abrechnung",
            "aktiv",
            "bemerkung",
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True

    def get_instance(self, instance_loader, row):
        try:
            stelle = self.fields["stelle"].clean(row)
            mitarbeiter = self.fields["mitarbeiter"].clean(row)
            beginn = self.fields["beginn"].clean(row)
        except ValueError:
            # Fehler werden beim eigentlichen Feld-Import gemeldet
            return None

        try:
            return Einsatz.objects.get(stelle=stelle, mitarbeiter=mitarbeiter, beginn=beginn)
        except Einsatz.DoesNotExist:
            return None
        except Einsatz.MultipleObjectsReturned:
            raise ValidationError(
                "Mehrere Einsätze mit gleicher Stelle, Personalnummer und Beginn gefunden."
            )

    def before_import_row(self, row, **kwargs):
        if not _text(row.get("Stellen-Id")):
            raise ValidationError("Stellen-Id darf nicht leer sein.")
        if not _text(row.get("Personalnummer")):
            raise ValidationError("Personalnummer darf nicht leer sein.")
        if not _text(row.get("Beginn")):
            raise ValidationError("Beginn darf nicht leer sein.")

        umfang = row.get("Umfang")
        if _text(umfang):
            wert = ProzentAnteilWidget().clean(umfang)
            if wert is not None and wert <= 0:
                raise ValidationError("Umfang muss größer als 0 sein.")

        beginn = DeutschesDatumWidget().clean(row.get("Beginn"))
        ende = DeutschesDatumWidget().clean(row.get("Ende"))
        if beginn and ende and ende < beginn:
            raise ValidationError("Ende darf nicht vor Beginn liegen.")

    def before_save_instance(self, instance, row, **kwargs):
        user = kwargs.get("user")
        if user is not None and not instance.angelegt_von:
            instance.angelegt_von = user
