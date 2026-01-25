from django.urls import path
from .views import *

urlpatterns = [
    path("", personal, name="personal"),
    path("<int:pk>/", person_detail, name='person_detail'),
    path("neu/", mitarbeiter_create, name="personal_create"),
    path("<int:pk>/bearbeiten/", mitarbeiter_update, name="personal_update"),
    path('<int:pk>/delete/', mitarbeiter_delete, name='mitarbeiter_delete'),
    path("dashboard", pers_dashboard, name="pers_dashboard"),

]