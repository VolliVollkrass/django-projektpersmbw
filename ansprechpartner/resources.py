from import_export import resources
from django.core.exceptions import ValidationError
from .models import Ansprechpartner


class AnsprechpartnerResource(resources.ModelResource):

    class Meta:
        model = Ansprechpartner
        fields = (
            "id",
            "vorname",
            "nachname",
            "geschlecht",
            "email",
            "telefon",
            "aktiv",
            "notiz",
        )
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True

    # 🔎 Individuelle Matching-Logik
    def get_instance(self, instance_loader, row):
        email = row.get("email")
        vorname = row.get("vorname")
        nachname = row.get("nachname")

        if email:
            qs = Ansprechpartner.objects.filter(email=email)
        else:
            qs = Ansprechpartner.objects.filter(
                vorname=vorname,
                nachname=nachname,
            )

        if qs.count() > 1:
            raise ValidationError(
                f"Mehrere Ansprechpartner gefunden für {vorname} {nachname}."
            )

        return qs.first()

    # 🔐 Validierung
    def before_import_row(self, row, **kwargs):

        if not row.get("vorname"):
            raise ValidationError("Vorname darf nicht leer sein.")

        if not row.get("nachname"):
            raise ValidationError("Nachname darf nicht leer sein.")

        if row.get("geschlecht") not in ["w", "m", "d"]:
            raise ValidationError("Geschlecht muss w, m oder d sein.")
