from django import forms
from .models import Einsatz

class EinsatzForm(forms.ModelForm):

    beginn = forms.DateField(
        required=True,
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"}
        )
    )

    ende = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"}
        )
    )

    class Meta:
        model = Einsatz
        fields = [
            "stelle", "mitarbeiter", "beginn", "ende", "umfang", "abrechnung",
            "aktiv", "bemerkung"
        ]

        widgets = {
            "bemerkung": forms.Textarea(attrs={"rows": 3}),
            "abrechnung": forms.CheckboxInput(
                attrs={"class": "toggle toggle-primary"}
            ),
            "aktiv": forms.CheckboxInput(
                attrs={"class": "checkbox checkbox-primary"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            # ❌ Checkboxen bekommen KEIN Input-Styling
            if isinstance(field.widget, forms.CheckboxInput):
                continue

            field.widget.attrs.update({
                "class": "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring focus:border-purple-800"
            })

        # 🔁 Datum korrekt anzeigen bei Edit
        if self.instance.pk:
            if self.instance.beginn:
                self.initial["beginn"] = self.instance.beginn.strftime("%Y-%m-%d")
            if self.instance.ende:
                self.initial["ende"] = self.instance.ende.strftime("%Y-%m-%d")



