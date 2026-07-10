from django.contrib import admin
from django.urls import path, include

from .views import protected_media

urlpatterns = [
    path('admin/', admin.site.urls),
    # Media (PDFs mit Personendaten) nur mit Login abrufbar
    path('media/<path:path>', protected_media, name='protected_media'),
    path("", include("home.urls")),
    path("auth/", include("userprofile.urls")),
    path("pers/", include("personal.urls")),
    path("traeger/", include("traeger.urls")),
    path("ansprech/", include("ansprechpartner.urls")),
    path("einsatz/", include("einsatz.urls")),
    path("beurteilung/", include("beurteilung.urls")),
    path("mbw/", include("mbw.urls")),
    path("daten/", include("datenaustausch.urls")),
]
