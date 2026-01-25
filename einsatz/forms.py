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
            "stelle", "mitarbeiter", "beginn", "ende", "umfang",
            "aktiv", "bemerkung"
        ]

        widgets = {
            "bemerkung": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring focus:border-purple-800"
            })

        # 🔁 Robust: sorgt dafür, dass bestehende Datumswerte korrekt angezeigt werden
        if self.instance.pk:
            if self.instance.beginn:
                self.initial["beginn"] = self.instance.beginn.strftime("%Y-%m-%d")
            if self.instance.ende:
                self.initial["ende"] = self.instance.ende.strftime("%Y-%m-%d")


