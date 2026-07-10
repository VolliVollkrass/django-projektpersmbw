from django.urls import path

from . import views

urlpatterns = [
    path("", views.uebersicht, name="datenaustausch"),
    path("vorlage/", views.vorlage_download, name="datenaustausch_vorlage"),
    path("export/", views.export_alle, name="datenaustausch_export"),
    path("export/<slug:slug>/", views.export_einzeln, name="datenaustausch_export_einzeln"),
    path("import/vorschau/", views.import_vorschau, name="datenaustausch_import_vorschau"),
    path("import/bestaetigen/", views.import_bestaetigen, name="datenaustausch_import_bestaetigen"),
    path("import/abbrechen/", views.import_abbrechen, name="datenaustausch_import_abbrechen"),
]
