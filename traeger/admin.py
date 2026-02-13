from django.contrib import admin
from .models import Traeger, Stelle, Einrichtung
from import_export.admin import ImportExportModelAdmin
from .resources import TraegerResource, EinrichtungResource, StelleResource



class StelleInline(admin.TabularInline):
    model = Stelle
    extra = 0
    show_change_link = True

@admin.register(Traeger)
class TraegerAdmin(ImportExportModelAdmin):
    resource_class = TraegerResource
    list_display = (
        "name",
        "art",
        "traeger_id",
        "haupt_ansprechpartner",
        "aktiv",
    )

    list_filter = ("art", "aktiv")
    search_fields = ("name", "traeger_id", "ort")
    ordering = ("name",)

    autocomplete_fields = ("haupt_ansprechpartner",)

    fieldsets = (
        ("Grunddaten", {
            "fields": ("name", "art", "traeger_id", "aktiv")
        }),
        ("Hauptansprechpartner", {
            "fields": ("haupt_ansprechpartner",)
        }),
        ("Adresse", {
            "fields": ("strasse", "plz", "ort")
        }),
        ("Verwaltung", {
            "fields": ( "bemerkung",)
        }),
        ("System", {
            "fields": ("erstellt_am", "geaendert_am")
        }),
    )

    readonly_fields = ("erstellt_am", "geaendert_am")



@admin.register(Stelle)
class StelleAdmin(ImportExportModelAdmin):
    resource_class = StelleResource
    # Spalten in der Listenansicht
    list_display = (
        "name",
        "stellen_id",
        "einrichtung",
        "position",
        "ort",
        "aktiv",
        "erstellt_am",
    )

    # Klickbare Spalten
    list_display_links = ("name", "stellen_id")

    # Filter rechte Seite
    list_filter = ("aktiv", "einrichtung", "ort")

    # Suchfeld oben
    search_fields = (
        "name",
        "stellen_id",
        "einrichtung__name",
        "ort",
        "strasse",
    )

    # Standardsortierung
    ordering = ("name",)

    # ManyToMany komfortabler machen

    # Felder schreibgeschützt
    readonly_fields = ("erstellt_am", "geaendert_am")

    # Struktur im Formular
    fieldsets = (
        ("Grunddaten", {
            "fields": ("einrichtung", "name", "position", "stellen_id", "aktiv")
        }),
        ("Adresse", {
            "fields": ("strasse", "plz", "ort"),
        }),
        ("Zuordnung", {
            "fields": ("ansprechpartner",),
        }),
        ("Bemerkung", {
            "fields": ("bemerkung",),
        }),
        ("System", {
            "fields": ("erstellt_am", "geaendert_am"),
        }),
    )

@admin.register(Einrichtung)
class EinrichtungAdmin(ImportExportModelAdmin):
    resource_class = EinrichtungResource
    list_display = (
        "name",
        "einrichtungs_id",
        "traeger",
        "ansprechpartner",
        "ort",
        "aktiv",
        "erstellt_am",
    )

    list_display_links = ("name", "einrichtungs_id")

    list_filter = ("aktiv", "traeger", "ort")

    search_fields = (
        "name",
        "einrichtungs_id",
        "traeger__name",
        "ort",
        "strasse",
    )

    ordering = ("name",)

    readonly_fields = ("erstellt_am", "geaendert_am")

    fieldsets = (
        ("Grunddaten", {
            "fields": ("traeger", "name", "einrichtungs_id", "aktiv")
        }),
        ("Adresse", {
            "fields": ("strasse", "plz", "ort", "ansprechpartner"),
        }),
        ("Bemerkung", {
            "fields": ("bemerkung", "versorgungsumlage"),
        }),
        ("System", {
            "fields": ("erstellt_am", "geaendert_am"),
        }),
    )