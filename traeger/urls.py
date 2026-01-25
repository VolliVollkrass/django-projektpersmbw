from django.urls import path
from .views import *

urlpatterns = [
    path("", traeger, name="traeger"),
    path("<int:pk>/", traeger_detail, name='traeger_detail'),
    path("neu/", traeger_create, name="traeger_create"),
    path("<int:pk>/edit/", traeger_edit, name="traeger_edit"),
    path('<int:pk>/delete/', traeger_delete, name='traeger_delete'),
    path("stellen/", stellen, name="stellen"),
    path("stellen/<int:pk>/", stellen_detail, name='stellen_detail'),
    path("stellen/neu/", stellen_create, name="stellen_create"),
    path("stellen/<int:pk>/edit/", stellen_edit, name="stellen_edit"),
    path('stellen/<int:pk>/delete/', stellen_delete, name='stellen_delete'),
    path("einrichtung/", einrichtung, name="einrichtung"),
    path("einrichtung/<int:pk>/", einrichtung_detail, name='einrichtung_detail'),
    path("einrichtung/neu/", einrichtung_create, name="einrichtung_create"),
    path("einrichtung/<int:pk>/edit/", einrichtung_edit, name="einrichtung_edit"),
    path('einrichtung/<int:pk>/delete/', einrichtung_delete, name='einrichtung_delete'),
]