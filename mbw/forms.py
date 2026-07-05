from django import forms

from .models import Fakturierungsvorgang, Innenauftrag


class InnenauftragForm(forms.ModelForm):
    class Meta:
        model = Innenauftrag
        fields = ["nummer", "bezeichnung", "aktiv", "bemerkung"]
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
            "besoldung_gesamt",
            "sap_auftragsnummer",
            "sap_erfasst_am",
            "kasse_uebergeben_am",
            "rechnungsnummer",
            "rechnung_pdf",
            "versandart",
            "versandt_am",
            "debitor_status",
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
