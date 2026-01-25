from django import forms
from .models import Mitarbeiter

class MitarbeiterForm(forms.ModelForm):

    geburtsdatum = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"}
        )
    )

    class Meta:
        model = Mitarbeiter
        fields = [
            "personalnummer", "geschlecht", "vorname", "nachname", "geburtsdatum",
            "email", "telefon_privat", "telefon_dienst", "strasse", "plz", "ort",
            "anstellungs_status", "dienststand", "status_besoldung", "status_stufe", 
            "familienstand", "kinder", "kindergeldberechtigt", "anspruch_voll",
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
            if self.instance.geburtsdatum:
                self.initial["geburtsdatum"] = self.instance.geburtsdatum.strftime("%Y-%m-%d")

