from django.contrib import admin

from .models import Fakturierungsvorgang, Innenauftrag, Quartalsabrechnung


@admin.register(Innenauftrag)
class InnenauftragAdmin(admin.ModelAdmin):
    list_display = ("nummer", "bezeichnung", "einsatz", "andock_art", "aktiv")
    list_filter = ("aktiv", "andock_art")
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
