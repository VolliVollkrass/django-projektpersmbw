from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EinsatzForm
from .models import Einsatz


@login_required
def einsatz(request):
    query = request.GET.get("q", "")
    einsaetze = Einsatz.objects.all()
    einsatz_anzahl = Einsatz.objects.count()

    if query:
        einsaetze = einsaetze.filter(
            Q(stelle__name__icontains=query)
            | Q(mitarbeiter__vorname__icontains=query)
            | Q(mitarbeiter__nachname__icontains=query)
            | Q(beginn__icontains=query)
            | Q(ende__icontains=query)
        )

    ctx = {"einsaetze": einsaetze, "einsatz_anzahl": einsatz_anzahl, "query": query}
    return render(request, "einsatz/einsatz.html", ctx)


@login_required
def einsatz_toggle_abrechnung(request, pk):
    einsatz = get_object_or_404(Einsatz, pk=pk)
    if request.method == "POST":
        einsatz.abrechnung = not einsatz.abrechnung
        einsatz.save(update_fields=["abrechnung", "aktualisiert_am"])
        status = "aktiv" if einsatz.abrechnung else "deaktiviert"
        messages.success(request, f"Abrechnung für Einsatz wurde {status}.")
    return redirect("einsatz")


@login_required
def einsatz_detail(request, pk):
    einsatz = get_object_or_404(Einsatz, pk=pk)
    return render(request, "einsatz/einsatz_detail.html", {"einsatz": einsatz})


@login_required
def einsatz_create(request):
    if request.method == "POST":
        form = EinsatzForm(request.POST)
        if form.is_valid():
            einsatz = form.save(commit=False)
            einsatz.angelegt_von = request.user
            einsatz.save()
            return redirect("einsatz_detail", pk=einsatz.pk)
    else:
        form = EinsatzForm()

    return render(request, "einsatz/einsatz_form.html", {"form": form})


@login_required
def einsatz_update(request, pk):
    einsatz = get_object_or_404(Einsatz, pk=pk)

    if request.method == "POST":
        form = EinsatzForm(request.POST, instance=einsatz)
        if form.is_valid():
            form.save()
            return redirect("einsatz_detail", pk=einsatz.pk)
    else:
        form = EinsatzForm(instance=einsatz)

    return render(
        request,
        "einsatz/einsatz_form.html",
        {"form": form, "einsatz": einsatz, "modus": "edit"},
    )


@login_required
def einsatz_delete(request, pk):
    einsatz = get_object_or_404(Einsatz, pk=pk)

    if request.method == "POST":
        confirm_text = request.POST.get("confirm_text")
        if confirm_text == "Löschen":
            einsatz.delete()
            messages.success(request, "Einsatz*in erfolgreich gelöscht.")
            return redirect("einsatz")

    return redirect("einsatz_detail", pk=einsatz.pk)
