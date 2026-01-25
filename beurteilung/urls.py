from django.urls import path
from . import views

urlpatterns = [
    path("evaluation/<uuid:token>/", views.evaluations_view, name="evaluation"),
    path(
    "evaluation/pdf/<int:evaluation_id>/",
    views.evaluation_pdf_view,
    name="evaluation_pdf"
),
]
