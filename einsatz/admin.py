from django.contrib import admin
from .models import Einsatz

# Register your models here.
@admin.register(Einsatz)
class EinsatzAdmin(admin.ModelAdmin):
    list_display = ("stelle", "mitarbeiter", "umfang_anzeige", "beginn", "ende", "abrechnung", "aktiv")

    def umfang_anzeige(self, obj):
        return f"{obj.umfang_prozent:.0f} %"
    umfang_anzeige.short_description = "Umfang"