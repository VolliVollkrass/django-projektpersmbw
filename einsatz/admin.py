from django.contrib import admin
from .models import Einsatz
from import_export.admin import ImportExportModelAdmin
from .resources import EinsatzResource


# Register your models here.
@admin.register(Einsatz)
class EinsatzAdmin(ImportExportModelAdmin):
    resource_class = EinsatzResource
    list_display = ("stelle", "mitarbeiter", "umfang_anzeige", "beginn", "ende", "abrechnung", "aktiv")

    def umfang_anzeige(self, obj):
        return f"{obj.umfang_prozent:.0f} %"
    umfang_anzeige.short_description = "Umfang"