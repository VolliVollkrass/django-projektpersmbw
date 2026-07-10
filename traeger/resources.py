from django.core.exceptions import ValidationError
from import_export import fields, resources

from ansprechpartner.models import Ansprechpartner
from datenaustausch.widgets import (
    AnsprechpartnerEmailWidget,
    ChoiceLabelWidget,
    JaNeinWidget,
    SammelIdWidget,
    TextWidget,
    TraegerIdWidget,
    VersorgungsumlageWidget,
    _text,
)
from .models import Einrichtung, Stelle, Traeger


def _plz_pruefen(row):
    plz = _text(row.get("PLZ"))
    if plz and (len(plz) != 5 or not plz.isdigit()):
        raise ValidationError("PLZ muss 5-stellig sein.")


class TraegerResource(resources.ModelResource):
    """Spalten = Blatt 'Träger' der Vorlage. Fachlicher Schlüssel: Träger-Id."""

    traeger_id = fields.Field(column_name="Träger-Id", attribute="traeger_id", widget=TextWidget())
    name = fields.Field(column_name="Name", attribute="name", widget=TextWidget())
    art = fields.Field(
        column_name="Art",
        attribute="art",
        widget=ChoiceLabelWidget(Traeger.TraegerArt.choices, default=Traeger.TraegerArt.SONSTIGE),
    )
    haupt_ansprechpartner = fields.Field(
        column_name="Haupt-Ansprechpartner (E-Mail)",
        attribute="haupt_ansprechpartner",
        widget=AnsprechpartnerEmailWidget(Ansprechpartner),
    )
    strasse = fields.Field(column_name="Straße", attribute="strasse", widget=TextWidget())
    plz = fields.Field(column_name="PLZ", attribute="plz", widget=TextWidget())
    ort = fields.Field(column_name="Ort", attribute="ort", widget=TextWidget())
    aktiv = fields.Field(column_name="Aktiv", attribute="aktiv", widget=JaNeinWidget(default=True))
    bemerkung = fields.Field(column_name="Bemerkung", attribute="bemerkung", widget=TextWidget())

    class Meta:
        model = Traeger
        import_id_fields = ("traeger_id",)
        fields = (
            "traeger_id",
            "name",
            "art",
            "haupt_ansprechpartner",
            "strasse",
            "plz",
            "ort",
            "aktiv",
            "bemerkung",
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True

    def before_import_row(self, row, **kwargs):
        if not _text(row.get("Träger-Id")):
            raise ValidationError("Träger-Id darf nicht leer sein.")
        if not _text(row.get("Name")):
            raise ValidationError("Name darf nicht leer sein.")
        _plz_pruefen(row)


class EinrichtungResource(resources.ModelResource):
    """Spalten = Blatt 'Einrichtungen'. Fachlicher Schlüssel: Einrichtungs-Id + Name
    (Sammel-Ids dürfen mehrfach vorkommen)."""

    einrichtungs_id = fields.Field(
        column_name="Einrichtungs-Id", attribute="einrichtungs_id", widget=TextWidget()
    )
    name = fields.Field(column_name="Name", attribute="name", widget=TextWidget())
    traeger = fields.Field(
        column_name="Träger-Id",
        attribute="traeger",
        widget=TraegerIdWidget(Traeger),
    )
    einrichtung_art = fields.Field(
        column_name="Art",
        attribute="einrichtung_art",
        widget=ChoiceLabelWidget(Einrichtung.EinrichtungsArt.choices),
    )
    strasse = fields.Field(column_name="Straße", attribute="strasse", widget=TextWidget())
    plz = fields.Field(column_name="PLZ", attribute="plz", widget=TextWidget())
    ort = fields.Field(column_name="Ort", attribute="ort", widget=TextWidget())
    ansprechpartner = fields.Field(
        column_name="Ansprechpartner (E-Mail)",
        attribute="ansprechpartner",
        widget=AnsprechpartnerEmailWidget(Ansprechpartner),
    )
    versorgungsumlage = fields.Field(
        column_name="Versorgungsumlage",
        attribute="versorgungsumlage",
        widget=VersorgungsumlageWidget(),
    )
    aktiv = fields.Field(column_name="Aktiv", attribute="aktiv", widget=JaNeinWidget(default=True))
    bemerkung = fields.Field(column_name="Bemerkung", attribute="bemerkung", widget=TextWidget())

    class Meta:
        model = Einrichtung
        import_id_fields = ("einrichtungs_id", "name")
        fields = (
            "einrichtungs_id",
            "name",
            "traeger",
            "einrichtung_art",
            "strasse",
            "plz",
            "ort",
            "ansprechpartner",
            "versorgungsumlage",
            "aktiv",
            "bemerkung",
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True

    def before_import_row(self, row, **kwargs):
        if not _text(row.get("Einrichtungs-Id")):
            raise ValidationError("Einrichtungs-Id darf nicht leer sein.")
        if not _text(row.get("Name")):
            raise ValidationError("Name darf nicht leer sein.")
        if not _text(row.get("Träger-Id")):
            raise ValidationError("Einrichtung benötigt einen Träger (Spalte 'Träger-Id').")
        _plz_pruefen(row)


class StelleResource(resources.ModelResource):
    """Spalten = Blatt 'Stellen'. Fachlicher Schlüssel: Stellen-Id + Name.

    Der Verweis auf die Einrichtung läuft über die Einrichtungs-Id; bei
    Sammel-Ids entscheidet die Spalte 'Einrichtung (Name)'.
    """

    stellen_id = fields.Field(column_name="Stellen-Id", attribute="stellen_id", widget=TextWidget())
    name = fields.Field(column_name="Name", attribute="name", widget=TextWidget())
    einrichtung = fields.Field(
        column_name="Einrichtungs-Id",
        attribute="einrichtung",
        widget=SammelIdWidget(
            Einrichtung,
            id_feld="einrichtungs_id",
            id_spalte="Einrichtungs-Id",
            name_spalte="Einrichtung (Name)",
            blatt_hinweis="Einrichtungen",
        ),
    )
    einrichtung_name = fields.Field(
        column_name="Einrichtung (Name)",
        attribute="einrichtung__name",
        readonly=True,
    )
    position = fields.Field(column_name="Position", attribute="position", widget=TextWidget())
    strasse = fields.Field(column_name="Straße", attribute="strasse", widget=TextWidget())
    plz = fields.Field(column_name="PLZ", attribute="plz", widget=TextWidget())
    ort = fields.Field(column_name="Ort", attribute="ort", widget=TextWidget())
    ansprechpartner = fields.Field(
        column_name="Ansprechpartner (E-Mail)",
        attribute="ansprechpartner",
        widget=AnsprechpartnerEmailWidget(Ansprechpartner),
    )
    aktiv = fields.Field(column_name="Aktiv", attribute="aktiv", widget=JaNeinWidget(default=True))
    bemerkung = fields.Field(column_name="Bemerkung", attribute="bemerkung", widget=TextWidget())

    class Meta:
        model = Stelle
        import_id_fields = ("stellen_id", "name")
        fields = (
            "stellen_id",
            "name",
            "einrichtung",
            "einrichtung_name",
            "position",
            "strasse",
            "plz",
            "ort",
            "ansprechpartner",
            "aktiv",
            "bemerkung",
        )
        export_order = fields
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True

    def before_import_row(self, row, **kwargs):
        if not _text(row.get("Stellen-Id")):
            raise ValidationError("Stellen-Id darf nicht leer sein.")
        if not _text(row.get("Name")):
            raise ValidationError("Name darf nicht leer sein.")
        if not _text(row.get("Einrichtungs-Id")):
            raise ValidationError("Stelle benötigt eine Einrichtung (Spalte 'Einrichtungs-Id').")
        _plz_pruefen(row)
