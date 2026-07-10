from django.core.exceptions import ValidationError
from import_export import fields, resources

from datenaustausch.widgets import (
    ChoiceLabelWidget,
    DeutschesDatumWidget,
    GanzzahlWidget,
    JaNeinWidget,
    TextWidget,
    _text,
)
from .models import Mitarbeiter


class MitarbeiterResource(resources.ModelResource):
    """Spalten = Blatt 'Mitarbeiter' der Vorlage. Fachlicher Schlüssel: Personalnummer."""

    personalnummer = fields.Field(
        column_name="Personalnummer", attribute="personalnummer", widget=TextWidget()
    )
    geschlecht = fields.Field(
        column_name="Geschlecht",
        attribute="geschlecht",
        widget=ChoiceLabelWidget(Mitarbeiter.Geschlecht.choices, default=Mitarbeiter.Geschlecht.M),
    )
    vorname = fields.Field(column_name="Vorname", attribute="vorname", widget=TextWidget())
    nachname = fields.Field(column_name="Nachname", attribute="nachname", widget=TextWidget())
    geburtsdatum = fields.Field(
        column_name="Geburtsdatum", attribute="geburtsdatum", widget=DeutschesDatumWidget()
    )
    email = fields.Field(column_name="E-Mail", attribute="email", widget=TextWidget())
    telefon_privat = fields.Field(
        column_name="Telefon privat", attribute="telefon_privat", widget=TextWidget()
    )
    telefon_dienst = fields.Field(
        column_name="Telefon dienstlich", attribute="telefon_dienst", widget=TextWidget()
    )
    strasse = fields.Field(column_name="Straße", attribute="strasse", widget=TextWidget())
    plz = fields.Field(column_name="PLZ", attribute="plz", widget=TextWidget())
    ort = fields.Field(column_name="Ort", attribute="ort", widget=TextWidget())
    anstellungs_status = fields.Field(
        column_name="Anstellung",
        attribute="anstellungs_status",
        widget=ChoiceLabelWidget(Mitarbeiter.Anstellung.choices, default=Mitarbeiter.Anstellung.OER),
    )
    dienststand = fields.Field(
        column_name="Dienststand",
        attribute="dienststand",
        widget=ChoiceLabelWidget(Mitarbeiter.Dienststand.choices, default=Mitarbeiter.Dienststand.DIAKON),
    )
    status_besoldung = fields.Field(
        column_name="Besoldungsgruppe",
        attribute="status_besoldung",
        widget=ChoiceLabelWidget(Mitarbeiter.Besoldung.choices, default=Mitarbeiter.Besoldung.A10),
    )
    status_stufe = fields.Field(
        column_name="Stufe", attribute="status_stufe", widget=GanzzahlWidget(default=4)
    )
    familienstand = fields.Field(
        column_name="Familienstand",
        attribute="familienstand",
        widget=ChoiceLabelWidget(
            Mitarbeiter.Familienstand.choices, default=Mitarbeiter.Familienstand.LEDIG
        ),
    )
    kinder = fields.Field(column_name="Kinder", attribute="kinder", widget=GanzzahlWidget(default=0))
    kindergeldberechtigt = fields.Field(
        column_name="Kindergeldberechtigt",
        attribute="kindergeldberechtigt",
        widget=JaNeinWidget(default=False),
    )
    anspruch_voll = fields.Field(
        column_name="Voller OFZ-Anspruch",
        attribute="anspruch_voll",
        widget=JaNeinWidget(default=False),
    )
    aktiv = fields.Field(column_name="Aktiv", attribute="aktiv", widget=JaNeinWidget(default=True))
    bemerkung = fields.Field(column_name="Bemerkung", attribute="bemerkung", widget=TextWidget())

    class Meta:
        model = Mitarbeiter
        import_id_fields = ("personalnummer",)
        fields = (
            "personalnummer",
            "geschlecht",
            "vorname",
            "nachname",
            "geburtsdatum",
            "email",
            "telefon_privat",
            "telefon_dienst",
            "strasse",
            "plz",
            "ort",
            "anstellungs_status",
            "dienststand",
            "status_besoldung",
            "status_stufe",
            "familienstand",
            "kinder",
            "kindergeldberechtigt",
            "anspruch_voll",
            "aktiv",
            "bemerkung",
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True

    def before_import_row(self, row, **kwargs):
        if not _text(row.get("Personalnummer")):
            raise ValidationError("Personalnummer darf nicht leer sein.")
        if not _text(row.get("Vorname")):
            raise ValidationError("Vorname darf nicht leer sein.")
        if not _text(row.get("Nachname")):
            raise ValidationError("Nachname darf nicht leer sein.")
        if not _text(row.get("Geburtsdatum")):
            raise ValidationError("Geburtsdatum darf nicht leer sein.")

        kinder = _text(row.get("Kinder"))
        if kinder and kinder.lstrip("-").isdigit() and int(kinder) < 0:
            raise ValidationError("Kinder darf nicht negativ sein.")

        plz = _text(row.get("PLZ"))
        if plz and (len(plz) != 5 or not plz.isdigit()):
            raise ValidationError("PLZ muss 5-stellig sein.")

    def before_save_instance(self, instance, row, **kwargs):
        user = kwargs.get("user")
        if user is not None and not instance.angelegt_von:
            instance.angelegt_von = user
