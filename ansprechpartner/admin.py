from django.contrib import admin
from .models import Ansprechpartner
from import_export.admin import ImportExportModelAdmin
from .resources import AnsprechpartnerResource



@admin.register(Ansprechpartner)
class AnsprechpartnerAdmin(ImportExportModelAdmin):
    resource_class = AnsprechpartnerResource
    list_display = (
        "nachname",
        "vorname",
        "email",
        "telefon",
        "aktiv",
    )

    list_filter = ("aktiv", "geschlecht")
    search_fields = ("vorname", "nachname", "email", "telefon")
    ordering = ("nachname", "vorname")

    fieldsets = (
        ("Persönliche Daten", {
            "fields": ("geschlecht", "vorname", "nachname")
        }),
        ("Kontakt", {
            "fields": ("email", "telefon")
        }),
        ("Status / Notizen", {
            "fields": ("aktiv", "notiz")
        }),
        ("System", {
            "fields": ("erstellt_am", "geaendert_am")
        }),
    )

    readonly_fields = ("erstellt_am", "geaendert_am")
