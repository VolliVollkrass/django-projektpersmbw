from django.urls import path
from .views import AktiveEinsaetzeListView, Mbw

urlpatterns = [
    path("", Mbw.as_view(), name="mbw"),
    path(
        "aktive-einsaetze/",
        AktiveEinsaetzeListView.as_view(),
        name="aktive_einsaetze"
    ),
]