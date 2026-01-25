from django import forms
from .models import Traeger, Stelle, Einrichtung, Ansprechpartner
from ansprechpartner.models import Ansprechpartner
from decimal import Decimal


class TraegerForm(forms.ModelForm):
    # Zusätzliche Felder für neuen Ansprechpartner
    neuer_ansprechpartner_vorname = forms.CharField(
        required=False, label="Vorname"
    )
    neuer_ansprechpartner_nachname = forms.CharField(
        required=False, label="Nachname"
    )
    neuer_ansprechpartner_email = forms.EmailField(
        required=False, label="E-Mail"
    )
    neuer_ansprechpartner_telefon = forms.CharField(
        required=False, label="Telefonnummer"
    )

    class Meta:
        model = Traeger
        fields = [
            "traeger_id", "art", "name", "strasse", "plz",
            "ort", "haupt_ansprechpartner", "aktiv", "bemerkung",
        ]
        widgets = {
            "bemerkung": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "w-full px-3 py-2 border rounded-field focus:outline-none focus:ring focus:border-primary"
            })

    def save(self, commit=True):
        # Speichern des Traegers
        traeger = super().save(commit=False)

        # Prüfen, ob neuer Ansprechpartner angelegt werden soll
        vorname = self.cleaned_data.get("neuer_ansprechpartner_vorname")
        nachname = self.cleaned_data.get("neuer_ansprechpartner_nachname")
        email = self.cleaned_data.get("neuer_ansprechpartner_email")
        telefon = self.cleaned_data.get("neuer_ansprechpartner_telefon")

        if vorname and nachname:
            neuer_ansprechpartner = Ansprechpartner.objects.create(
                vorname=vorname,
                nachname=nachname,
                email=email,
                telefon=telefon
            )
            traeger.haupt_ansprechpartner = neuer_ansprechpartner

        if commit:
            traeger.save()

        return traeger


class StellenForm(forms.ModelForm):
    neuer_ansprechpartner_vorname = forms.CharField(required=False, label="Vorname")
    neuer_ansprechpartner_nachname = forms.CharField(required=False, label="Nachname")
    neuer_ansprechpartner_email = forms.EmailField(required=False, label="E-Mail")
    neuer_ansprechpartner_telefon = forms.CharField(required=False, label="Telefonnummer")

    class Meta:
        model = Stelle
        fields = [
            "einrichtung", "name", "stellen_id", "strasse", "plz",
            "ort", "ansprechpartner", "position", "aktiv", "bemerkung",
        ]
        widgets = {
            "bemerkung": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "w-full px-3 py-2 border rounded-field focus:outline-none focus:ring focus:border-primary"
            })

    def save(self, commit=True):
        stelle = super().save(commit=False)

        # Neue Person aus Zusatzfeldern
        vorname = self.cleaned_data.get("neuer_ansprechpartner_vorname")
        nachname = self.cleaned_data.get("neuer_ansprechpartner_nachname")
        email = self.cleaned_data.get("neuer_ansprechpartner_email")
        telefon = self.cleaned_data.get("neuer_ansprechpartner_telefon")

        if vorname and nachname:
            neuer_ansprechpartner = Ansprechpartner.objects.create(
                vorname=vorname,
                nachname=nachname,
                email=email,
                telefon=telefon
            )
            # ✅ FK setzen statt add()
            stelle.ansprechpartner = neuer_ansprechpartner

        if commit:
            stelle.save()

        return stelle


class EinrichtungForm(forms.ModelForm):
    # Zusätzliche Felder für neuen Ansprechpartner
    neuer_ansprechpartner_vorname = forms.CharField(
        required=False, label="Vorname"
    )
    neuer_ansprechpartner_nachname = forms.CharField(
        required=False, label="Nachname"
    )
    neuer_ansprechpartner_email = forms.EmailField(
        required=False, label="E-Mail"
    )
    neuer_ansprechpartner_telefon = forms.CharField(
        required=False, label="Telefonnummer"
    )

    class Meta:
        model = Einrichtung
        fields = [
            "traeger", "einrichtungs_id", "einrichtung_art", "name", "strasse", "plz",
            "ort", "ansprechpartner", "versorgungsumlage", "aktiv", "bemerkung",
        ]
        widgets = {
            "bemerkung": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "w-full px-3 py-2 border rounded-field focus:outline-none focus:ring focus:border-primary"
            })

    def save(self, commit=True):
        # Speichern der einrichtung
        einrichtung = super().save(commit=False)

        # Prüfen, ob neuer Ansprechpartner angelegt werden soll
        vorname = self.cleaned_data.get("neuer_ansprechpartner_vorname")
        nachname = self.cleaned_data.get("neuer_ansprechpartner_nachname")
        email = self.cleaned_data.get("neuer_ansprechpartner_email")
        telefon = self.cleaned_data.get("neuer_ansprechpartner_telefon")

        if vorname and nachname:
            neuer_ansprechpartner = Ansprechpartner.objects.create(
                vorname=vorname,
                nachname=nachname,
                email=email,
                telefon=telefon
            )
            einrichtung.ansprechpartner = neuer_ansprechpartner

        if commit:
            einrichtung.save()

        return einrichtung