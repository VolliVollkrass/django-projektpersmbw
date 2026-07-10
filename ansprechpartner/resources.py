from django.core.exceptions import ValidationError
from import_export import fields, resources

from datenaustausch.widgets import ChoiceLabelWidget, JaNeinWidget, TextWidget, _text
from .models import GESCHLECHT, Ansprechpartner


class AnsprechpartnerResource(resources.ModelResource):
    """Spalten = Blatt 'Ansprechpartner' der Import-Vorlage.

    Fachlicher Schlüssel: E-Mail (Fallback: Vorname + Nachname).
    """

    vorname = fields.Field(column_name="Vorname", attribute="vorname", widget=TextWidget())
    nachname = fields.Field(column_name="Nachname", attribute="nachname", widget=TextWidget())
    geschlecht = fields.Field(
        column_name="Geschlecht",
        attribute="geschlecht",
        widget=ChoiceLabelWidget(GESCHLECHT, default="m"),
    )
    email = fields.Field(column_name="E-Mail", attribute="email", widget=TextWidget())
    telefon = fields.Field(column_name="Telefon", attribute="telefon", widget=TextWidget())
    notiz = fields.Field(column_name="Notiz", attribute="notiz", widget=TextWidget())
    aktiv = fields.Field(column_name="Aktiv", attribute="aktiv", widget=JaNeinWidget(default=True))

    class Meta:
        model = Ansprechpartner
        import_id_fields = ()
        fields = ("vorname", "nachname", "geschlecht", "email", "telefon", "notiz", "aktiv")
        export_order = fields
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True

    def get_instance(self, instance_loader, row):
        email = _text(row.get("E-Mail"))
        vorname = _text(row.get("Vorname"))
        nachname = _text(row.get("Nachname"))

        if email:
            qs = Ansprechpartner.objects.filter(email__iexact=email)
        else:
            qs = Ansprechpartner.objects.filter(
                vorname__iexact=vorname, nachname__iexact=nachname
            )

        if qs.count() > 1:
            raise ValidationError(
                f"Mehrere Ansprechpartner gefunden für {vorname} {nachname}."
            )
        return qs.first()

    def before_import_row(self, row, **kwargs):
        if not _text(row.get("Vorname")):
            raise ValidationError("Vorname darf nicht leer sein.")
        if not _text(row.get("Nachname")):
            raise ValidationError("Nachname darf nicht leer sein.")
