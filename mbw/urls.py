from django.urls import path

from .views import (
    abrechnungsliste,
    fakturierung_bearbeiten,
    fakturierungsliste,
    aktive_einsaetze,
    innenauftrag_create,
    innenauftrag_freigeben,
    innenauftrag_update,
    innenauftrag_zuweisen,
    innenauftraege,
    mbw,
    quartalsabrechnung_buchen,
    quartalsuebersicht,
)

urlpatterns = [
    path("", mbw, name="mbw"),
    path("aktive-einsaetze/", aktive_einsaetze, name="aktive_einsaetze"),
    path("abrechnung/", abrechnungsliste, name="abrechnungsliste"),
    path("innenauftraege/", innenauftraege, name="innenauftraege"),
    path("innenauftraege/neu/", innenauftrag_create, name="innenauftrag_create"),
    path("innenauftraege/<int:pk>/bearbeiten/", innenauftrag_update, name="innenauftrag_update"),
    path("innenauftraege/<int:pk>/freigeben/", innenauftrag_freigeben, name="innenauftrag_freigeben"),
    path("abrechnung/<int:pk>/innenauftrag-zuweisen/", innenauftrag_zuweisen, name="innenauftrag_zuweisen"),
    path("quartale/", quartalsuebersicht, name="quartalsuebersicht"),
    path("quartale/<int:pk>/buchen/", quartalsabrechnung_buchen, name="quartalsabrechnung_buchen"),
    path("fakturierung/", fakturierungsliste, name="fakturierungsliste"),
    path("fakturierung/<int:pk>/bearbeiten/", fakturierung_bearbeiten, name="fakturierung_bearbeiten"),
]
