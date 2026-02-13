from django.urls import path
from .views import abrechnungsliste, AktiveEinsaetzeListView, mbw

urlpatterns = [
    path("", mbw, name="mbw"),
    path("abrechnung/", abrechnungsliste, name="abrechnungsliste"),
    path(
        "aktive-einsaetze/",
        AktiveEinsaetzeListView.as_view(),
        name="aktive_einsaetze"
    ),
]