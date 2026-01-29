from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from django.utils.timezone import now
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required

#from .forms import EinsatzForm
from einsatz.models import Einsatz  


class AktiveEinsaetzeListView(ListView):
    model = Einsatz
    template_name = "mbw/aktive_einsaetze_list.html"
    context_object_name = "einsaetze"

    def get_queryset(self):
        heute = now().date()

        return Einsatz.objects.filter(
            aktiv=True
        ).filter(
            Q(ende__isnull=True) | Q(ende__gte=heute)
        ).select_related(
            "stelle", "mitarbeiter"
        ).order_by("beginn")


