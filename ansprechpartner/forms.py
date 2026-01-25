from django import forms
from .models import Ansprechpartner

class AnsprechForm(forms.ModelForm):

    class Meta:
        model = Ansprechpartner
        fields = [
            "geschlecht", "vorname", "nachname",
            "email", "telefon",
            "aktiv", "notiz"
        ]

        widgets = {
            "notiz": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring focus:border-purple-800"
            })