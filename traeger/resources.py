from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from django.core.exceptions import ValidationError
from .models import Traeger, Einrichtung, Stelle
from ansprechpartner.models import Ansprechpartner


class TraegerResource(resources.ModelResource):

    haupt_ansprechpartner = fields.Field(
        column_name="haupt_ansprechpartner",
        attribute="haupt_ansprechpartner",
        widget=ForeignKeyWidget(Ansprechpartner, "id"),
    )

    class Meta:
        model = Traeger
        import_id_fields = ("id",)
        fields = (
            "id",
            "name",
            "art",
            "traeger_id",
            "haupt_ansprechpartner",
            "strasse",
            "plz",
            "ort",
            "aktiv",
            "bemerkung",
        )
        clean_model_instances = True
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        # Name Pflicht
        if not row.get("name"):
            raise ValidationError("Name darf nicht leer sein.")

        # PLZ prüfen
        plz = row.get("plz")
        if plz and len(str(plz)) != 5:
            raise ValidationError("PLZ muss 5-stellig sein.")


class EinrichtungResource(resources.ModelResource):

    traeger = fields.Field(
        column_name="traeger",
        attribute="traeger",
        widget=ForeignKeyWidget(Traeger, "id"),
    )

    ansprechpartner = fields.Field(
        column_name="ansprechpartner",
        attribute="ansprechpartner",
        widget=ForeignKeyWidget(Ansprechpartner, "id"),
    )

    class Meta:
        model = Einrichtung
        import_id_fields = ("id",)
        fields = (
            "id",
            "traeger",
            "name",
            "einrichtung_art",
            "einrichtungs_id",
            "strasse",
            "plz",
            "ort",
            "ansprechpartner",
            "versorgungsumlage",
            "aktiv",
            "bemerkung",
        )
        clean_model_instances = True
        skip_unchanged = True

    def before_import_row(self, row, **kwargs):
        if not row.get("name"):
            raise ValidationError("Name darf nicht leer sein.")

        if not row.get("traeger"):
            raise ValidationError("Einrichtung benötigt einen Träger.")

        plz = row.get("plz")
        if plz and len(str(plz)) != 5:
            raise ValidationError("PLZ muss 5-stellig sein.")


class StelleResource(resources.ModelResource):

    einrichtung = fields.Field(
        column_name="einrichtung",
        attribute="einrichtung",
        widget=ForeignKeyWidget(Einrichtung, "id"),
    )

    ansprechpartner = fields.Field(
        column_name="ansprechpartner",
        attribute="ansprechpartner",
        widget=ForeignKeyWidget(Ansprechpartner, "id"),
    )

    class Meta:
        model = Stelle
        import_id_fields = ("id",)
        fields = (
            "id",
            "einrichtung",
            "name",
            "stellen_id",
            "strasse",
            "plz",
            "ort",
            "ansprechpartner",
            "position",
            "aktiv",
            "bemerkung",
        )
        clean_model_instances = True
        skip_unchanged = True

    def before_import_row(self, row, **kwargs):
        if not row.get("name"):
            raise ValidationError("Name darf nicht leer sein.")

        if not row.get("einrichtung"):
            raise ValidationError("Stelle benötigt eine Einrichtung.")

        plz = row.get("plz")
        if plz and len(str(plz)) != 5:
            raise ValidationError("PLZ muss 5-stellig sein.")
