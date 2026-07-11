from django.contrib import admin

from .models import (
    Beihilfesatz,
    Besoldungsbetrag,
    Besoldungstabelle,
    Debitor,
    Fakturierungsvorgang,
    Familienzuschlagtabelle,
    Familienzuschlagzeile,
    FZKinderErhoehung,
    Innenauftrag,
    Mietenstufe,
    Quartalsabrechnung,
    Zulagensatz,
)


@admin.register(Innenauftrag)
class InnenauftragAdmin(admin.ModelAdmin):
    list_display = ("nummer", "bezeichnung", "kostenstelle", "debitor", "einsatz", "andock_art", "aktiv")
    list_filter = ("aktiv", "andock_art", "kostenstelle")
    search_fields = (
        "nummer",
        "bezeichnung",
        "einsatz__stelle__name",
        "einsatz__mitarbeiter__vorname",
        "einsatz__mitarbeiter__nachname",
    )


@admin.register(Quartalsabrechnung)
class QuartalsabrechnungAdmin(admin.ModelAdmin):
    list_display = ("jahr", "quartal", "art", "einsatz", "verbucht_am")
    list_filter = ("jahr", "quartal", "art")
    search_fields = (
        "einsatz__stelle__name",
        "einsatz__mitarbeiter__vorname",
        "einsatz__mitarbeiter__nachname",
        "einsatz__innenauftrag__nummer",
    )


@admin.register(Debitor)
class DebitorAdmin(admin.ModelAdmin):
    list_display = ("name", "sap_nummer", "ort", "traeger", "aktiv")
    list_filter = ("aktiv",)
    search_fields = ("name", "name2", "sap_nummer", "ort", "traeger__name")


class BesoldungsbetragInline(admin.TabularInline):
    model = Besoldungsbetrag
    extra = 0


@admin.register(Besoldungstabelle)
class BesoldungstabelleAdmin(admin.ModelAdmin):
    list_display = ("gueltig_ab", "erhoehung_prozent")
    inlines = [BesoldungsbetragInline]


class FamilienzuschlagzeileInline(admin.TabularInline):
    model = Familienzuschlagzeile
    extra = 0


class FZKinderErhoehungInline(admin.TabularInline):
    model = FZKinderErhoehung
    extra = 0


@admin.register(Familienzuschlagtabelle)
class FamilienzuschlagtabelleAdmin(admin.ModelAdmin):
    list_display = ("gueltig_ab", "erhoehung_prozent")
    inlines = [FamilienzuschlagzeileInline, FZKinderErhoehungInline]


@admin.register(Zulagensatz)
class ZulagensatzAdmin(admin.ModelAdmin):
    list_display = ("art", "variante", "gueltig_ab", "betrag")
    list_filter = ("art",)


@admin.register(Beihilfesatz)
class BeihilfesatzAdmin(admin.ModelAdmin):
    list_display = ("jahr", "tarif", "kategorie", "alter_bis", "satz")
    list_filter = ("jahr", "tarif")


@admin.register(Mietenstufe)
class MietenstufeAdmin(admin.ModelAdmin):
    list_display = ("name", "art", "stufe")
    list_filter = ("art", "stufe")
    search_fields = ("name",)


@admin.register(Fakturierungsvorgang)
class FakturierungsvorgangAdmin(admin.ModelAdmin):
    list_display = (
        "jahr",
        "einsatz",
        "sap_auftragsnummer",
        "rechnungsnummer",
        "versandart",
        "debitor_status",
    )
    list_filter = ("jahr", "versandart", "debitor_status")
    search_fields = (
        "einsatz__stelle__name",
        "einsatz__mitarbeiter__vorname",
        "einsatz__mitarbeiter__nachname",
        "sap_auftragsnummer",
        "rechnungsnummer",
    )
