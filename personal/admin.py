from django.contrib import admin
from .models import Mitarbeiter
from traeger.models import Stelle
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin

#from einsatz.models import Einsatz

#class EinsatzInline(admin.TabularInline):
#    model = Einsatz
#    extra = 0
#    show_change_link = True


class MitarbeiterResource(resources.ModelResource):
    def before_import_row(self, row, **kwargs):
        if not row.get("personalnummer"):
            raise ValueError("Personalnummer fehlt")

        if row.get("kinder", 0) < 0:
            raise ValueError("Kinder darf nicht negativ sein")
        
    def before_save_instance(self, instance, row, **kwargs):
        user = kwargs.get("user")
        if not instance.angelegt_von:
            instance.angelegt_von = user


    class Meta:
        model = Mitarbeiter
        import_id_fields = ('personalnummer',)  # <- extrem wichtig (Update statt Duplikate)
        skip_unchanged = True
        report_skipped = True
        use_bulk = True
        batch_size = 500


class StelleInline(admin.TabularInline):
    model = Stelle
    extra = 0
    show_change_link = True

@admin.register(Mitarbeiter)
class MitarbeiterAdmin(ImportExportModelAdmin):

    # ----------------- Listenansicht -----------------
    resource_class = MitarbeiterResource
    list_display = (
        "personalnummer",
        "nachname",
        "vorname",
        "geschlecht",
        "dienststand",
        "status_besoldung",
        "aktiv",
    )

    list_filter = (
        "aktiv",
        "dienststand",
        "status_besoldung",
        "anstellungs_status",
        "familienstand",
    )

    search_fields = (
        "personalnummer",
        "vorname",
        "nachname",
        "email",
        "telefon_privat",
        "telefon_dienst",
    )

    ordering = ("nachname", "vorname")

    # ----------------- Formulare -----------------
    fieldsets = (
        ("Grunddaten", {
            "fields": ("personalnummer", "vorname", "nachname", "geschlecht", "geburtsdatum")
        }),
        ("Kontaktdaten", {
            "fields": ("email", "telefon_privat", "telefon_dienst", "strasse", "plz", "ort")
        }),
        ("Dienstrechtlicher Status", {
            "fields": ("anstellungs_status", "dienststand", "status_besoldung", "status_stufe")
        }),
        ("Familie / Zuschläge", {
            "fields": ("familienstand", "kinder", "kindergeldberechtigt", "anspruch_voll")
        }),
        ("Verwaltung", {
            "fields": ("aktiv", "bemerkung", "angelegt_von")
        }),
        ("System", {
            "fields": ("angelegt_am", "aktualisiert_am")
        }),
    )
    #inlines = [StelleInline] #[EinsatzInline, StelleInline] So dann mit Einsatz

    readonly_fields = ("angelegt_am", "aktualisiert_am")

    # ----------------- Autocomplete / Filter -----------------
    autocomplete_fields = ("angelegt_von",)

    # Optional: verbessertes Layout für viele Felder
    # filter_horizontal = ()  # Wenn ManyToMany-Felder später hinzukommen

