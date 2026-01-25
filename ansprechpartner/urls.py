from django.urls import path
from .views import *

urlpatterns = [
    path("", ansprech, name="ansprech"),
    path("<int:pk>/", ansprech_detail, name='ansprech_detail'),
    path("neu/", ansprech_create, name="ansprech_create"),
    path("<int:pk>/bearbeiten/", ansprech_update, name="ansprech_update"),
    path('<int:pk>/delete/', ansprech_delete, name='ansprech_delete')
    ]