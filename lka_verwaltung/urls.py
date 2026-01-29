from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("home.urls")),
    path("auth/", include("userprofile.urls")),
    path("pers/", include("personal.urls")),
    path("traeger/", include("traeger.urls")),
    path("ansprech/", include("ansprechpartner.urls")),
    path("einsatz/", include("einsatz.urls")),
    path("beurteilung/", include("beurteilung.urls")),
    path("mbw/", include("mbw.urls")),
]
