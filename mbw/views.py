from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, TemplateView
from django.utils.timezone import now
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

#from .forms import EinsatzForm
from einsatz.models import Einsatz  

@login_required
def mbw(request):
    return render(request, "mbw/mbw.html")


class AktiveEinsaetzeListView(LoginRequiredMixin, ListView):
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

@login_required
def abrechnungsliste(request):
    query = request.GET.get("q", "")
    einsaetze = Einsatz.objects.filter(abrechnung=True).select_related(
        "stelle", "mitarbeiter"
    ).order_by("beginn")

    if query:
        einsaetze = einsaetze.filter(
            Q(stelle__name__icontains=query)
            | Q(mitarbeiter__vorname__icontains=query)
            | Q(mitarbeiter__nachname__icontains=query)
            | Q(beginn__icontains=query)
            | Q(ende__icontains=query)
        )

    context = {
        "einsaetze": einsaetze,
        "query": query,
        "einsatz_anzahl": einsaetze.count(),
    }
    return render(request, "mbw/abrechnungsliste.html", context)