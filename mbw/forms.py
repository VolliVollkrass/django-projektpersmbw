from django import forms

from .models import Debitor, Fakturierungsvorgang, Innenauftrag, Zahlungseingang

FELD_KLASSE = "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring focus:border-purple-800"


class DebitorForm(forms.ModelForm):
    class Meta:
        model = Debitor
        fields = [
            "sap_nummer", "name", "name2", "anschriftperson",
            "strasse", "plz", "ort", "email", "versandweg",
            "traeger", "aktiv", "bemerkung",
        ]
        widgets = {
            "bemerkung": forms.Textarea(attrs={"rows": 3}),
            "aktiv": forms.CheckboxInput(attrs={"class": "checkbox checkbox-primary"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            field.widget.attrs.update({"class": FELD_KLASSE})


class TabellenErhoehungForm(forms.Form):
    gueltig_ab = forms.DateField(
        label="Gültig ab", widget=forms.DateInput(attrs={"type": "date"})
    )
    prozent = forms.DecimalField(
        label="Erhöhung in %", max_digits=5, decimal_places=2, min_value=0, max_value=100
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            field.widget.attrs.update({"class": FELD_KLASSE})


class InnenauftragForm(forms.ModelForm):
    class Meta:
        model = Innenauftrag
        fields = ["nummer", "bezeichnung", "kostenstelle", "debitor", "aktiv", "bemerkung"]
        widgets = {
            "bemerkung": forms.Textarea(attrs={"rows": 3}),
            "aktiv": forms.CheckboxInput(attrs={"class": "checkbox checkbox-primary"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            field.widget.attrs.update(
                {
                    "class": "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring focus:border-purple-800"
                }
            )


class FakturierungsvorgangForm(forms.ModelForm):
    class Meta:
        model = Fakturierungsvorgang
        fields = [
            "debitor",
            "abschlag_quartal",
            "besoldung_gesamt",
            "sap_auftragsnummer",
            "sap_erfasst_am",
            "kasse_uebergeben_am",
            "rechnungsnummer",
            "rechnung_pdf",
            "versandart",
            "versandt_am",
            "debitor_geprueft_am",
            "bemerkung",
        ]
        widgets = {
            "sap_erfasst_am": forms.DateInput(attrs={"type": "date"}),
            "kasse_uebergeben_am": forms.DateInput(attrs={"type": "date"}),
            "versandt_am": forms.DateInput(attrs={"type": "date"}),
            "debitor_geprueft_am": forms.DateInput(attrs={"type": "date"}),
            "bemerkung": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({"class": "file-input file-input-bordered w-full"})
                continue
            field.widget.attrs.update(
                {
                    "class": "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring focus:border-purple-800"
                }
            )


class ZahlungseingangForm(forms.ModelForm):
    class Meta:
        model = Zahlungseingang
        fields = ["datum", "betrag", "bemerkung"]
        widgets = {
            "datum": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            field.widget.attrs.update({"class": FELD_KLASSE})


class PKImportForm(forms.Form):
    datei = forms.FileField(
        label="SAP-Auswertung",
        help_text="Dynamische Listenausgabe aus SAP (Textdatei, UTF-16, tabgetrennt)",
        widget=forms.FileInput(attrs={"class": "file-input file-input-bordered w-full"}),
    )
    bemerkung = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "class": FELD_KLASSE}),
    )
