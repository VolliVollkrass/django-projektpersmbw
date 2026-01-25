from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from .forms import MitarbeiterForm
from .models import Mitarbeiter
from django.utils import timezone
from django.db.models import Prefetch
from einsatz.models import Einsatz

# Create your views here.
@login_required
def pers_dashboard(request):
    return render(request, "personal/pers_dashboard.html" )


@login_required
def personal(request):
    query = request.GET.get("q", "")
    heute = timezone.now().date()
    gesamt_anzahl = Mitarbeiter.objects.count()

    
    aktuelle_einsaetze = Einsatz.objects.filter(
        aktiv=True,
        beginn__lte=heute
    ).filter(
        Q(ende__isnull=True) | Q(ende__gte=heute)
    ).select_related("stelle")

    mitarbeiters = Mitarbeiter.objects.prefetch_related(
        Prefetch("einsaetze", queryset=aktuelle_einsaetze)
    )

    if query:
        mitarbeiters = mitarbeiters.filter(
            Q(personalnummer__icontains=query) |
            Q(vorname__icontains=query) |
            Q(nachname__icontains=query)
        )

    ctx = {
        'mitarbeiters':mitarbeiters,
        'mitarbeiter_anzahl':gesamt_anzahl,
        "query": query
    }
    return render(request, "personal/personal.html", ctx )

@login_required
def person_detail(request, pk):
    mitarbeiter = get_object_or_404(Mitarbeiter, pk=pk)
    return render(request, 'personal/person_detail.html', {'mitarbeiter': mitarbeiter})

@login_required
def mitarbeiter_create(request):
    if request.method == "POST":
        form = MitarbeiterForm(request.POST)
        if form.is_valid():
            mitarbeiter = form.save(commit=False)
            mitarbeiter.angelegt_von = request.user
            mitarbeiter.save()
            return redirect("person_detail", pk=mitarbeiter.pk)
    else:
        form = MitarbeiterForm()

    return render(request, "personal/personal_form.html", {"form": form})

@login_required
def mitarbeiter_update(request, pk):
    mitarbeiter = get_object_or_404(Mitarbeiter, pk=pk)

    if request.method == "POST":
        form = MitarbeiterForm(request.POST, instance=mitarbeiter)
        if form.is_valid():
            form.save()
            return redirect("person_detail", pk=mitarbeiter.pk)
    else:
        form = MitarbeiterForm(instance=mitarbeiter)

    return render(request, "personal/personal_form.html", {
        "form": form,
        "mitarbeiter": mitarbeiter,
        "modus": "edit"
    })

@login_required
def mitarbeiter_delete(request, pk):
    mitarbeiter = get_object_or_404(Mitarbeiter, pk=pk)

    if request.method == "POST":
        confirm_text = request.POST.get("confirm_text")
        if confirm_text == "Löschen":
            mitarbeiter.delete()
            messages.success(request, f'Mitarbeiter*in erfolgreich gelöscht.')
            return redirect("personal")  # anpassen an deine URL

    return redirect("person_detail", pk=mitarbeiter.pk)



