from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, DateWidget
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Einsatz
from traeger.models import Stelle
from personal.models import Mitarbeiter
from decimal import Decimal


class EinsatzResource(resources.ModelResource):

    stelle = fields.Field(
        column_name="stelle",
        attribute="stelle",
        widget=ForeignKeyWidget(Stelle, "id"),
    )

    mitarbeiter = fields.Field(
        column_name="mitarbeiter",
        attribute="mitarbeiter",
        widget=ForeignKeyWidget(Mitarbeiter, "personalnummer"),
    )

    angelegt_von = fields.Field(
        column_name="angelegt_von",
        attribute="angelegt_von",
        widget=ForeignKeyWidget(User, "username"),
    )

    beginn = fields.Field(
        column_name="beginn",
        attribute="beginn",
        widget=DateWidget(format="%Y-%m-%d"),
    )

    ende = fields.Field(
        column_name="ende",
        attribute="ende",
        widget=DateWidget(format="%Y-%m-%d"),
    )

    class Meta:
        model = Einsatz
        fields = (
            "id",
            "stelle",
            "mitarbeiter",
            "beginn",
            "ende",
            "umfang",
            "abrechnung",
            "aktiv",
            "bemerkung",
            "angelegt_von",
        )
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True

    def get_instance(self, instance_loader, row):
        stelle = row.get("stelle")
        mitarbeiter = row.get("mitarbeiter")
        beginn = row.get("beginn")

        try:
            return Einsatz.objects.get(
                stelle_id=stelle,
                mitarbeiter_id=mitarbeiter,
                beginn=beginn,
            )
        except Einsatz.DoesNotExist:
            return None
        except Einsatz.MultipleObjectsReturned:
            raise ValidationError(
                "Mehrere Einsätze mit gleicher Stelle, Mitarbeiter und Beginn gefunden."
            )

    def before_import_row(self, row, **kwargs):

        if not row.get("stelle"):
            raise ValidationError("Stelle darf nicht leer sein.")

        if not row.get("mitarbeiter"):
            raise ValidationError("Mitarbeiter darf nicht leer sein.")

        if not row.get("beginn"):
            raise ValidationError("Beginn darf nicht leer sein.")

        # Umfang prüfen
        umfang = row.get("umfang")
        if umfang:
            try:
                if Decimal(umfang) <= 0:
                    raise ValidationError("Umfang muss größer als 0 sein.")
            except:
                raise ValidationError("Ungültiger Wert für Umfang.")

        # Datumslogik prüfen
        beginn = row.get("beginn")
        ende = row.get("ende")

        if beginn and ende and ende < beginn:
            raise ValidationError("Ende darf nicht vor Beginn liegen.")
