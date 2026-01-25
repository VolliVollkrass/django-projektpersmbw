from django.urls import path
from .views import *

urlpatterns = [
    path("", einsatz, name="einsatz"),
    path("<int:pk>/", einsatz_detail, name='einsatz_detail'),
    path("neu/", einsatz_create, name="einsatz_create"),
    path("<int:pk>/bearbeiten/", einsatz_update, name="einsatz_update"),
    path('<int:pk>/delete/', einsatz_delete, name='einsatz_delete'),
]