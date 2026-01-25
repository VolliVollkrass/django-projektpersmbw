from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from .models import Traeger, Stelle, Einrichtung
from .forms import TraegerForm, StellenForm, EinrichtungForm

# Create your views here.
@login_required
def traeger(request):
    query = request.GET.get("q", "")
    traegers = Traeger.objects.all()
    traeger_anzahl = Traeger.objects.count()

    if query:
        traegers = traegers.filter(
            Q(name__icontains=query) |
            Q(traeger_id__icontains=query) |
            Q(art__icontains=query)
        )
    ctx = {
        'traegers':traegers,
        'traeger_anzahl':traeger_anzahl,
        "query": query
    }
    return render(request, "traeger/traeger.html", ctx )

@login_required
def traeger_detail(request, pk):
    traeger = get_object_or_404(Traeger, pk=pk)
    return render(request, 'traeger/traeger_detail.html', {'traeger': traeger})

@login_required
def traeger_create(request):
    if request.method == "POST":
        form = TraegerForm(request.POST)
        if form.is_valid():
            traeger = form.save(commit=False)
            # Optional: Wenn du ein angelegt_von Feld hast
            # traeger.angelegt_von = request.user
            traeger.save()
            return redirect("traeger")
    else:
        form = TraegerForm()

    return render(request, "traeger/traeger_form.html", {"form": form, "modus": "create"})

@login_required
def traeger_edit(request, pk):
    traeger = get_object_or_404(Traeger, pk=pk)

    if request.method == "POST":
        form = TraegerForm(request.POST, instance=traeger)
        if form.is_valid():
            form.save()
            return redirect("traeger")  # zurück zur Übersicht
    else:
        form = TraegerForm(instance=traeger)

    return render(request, "traeger/traeger_form.html", {"form": form, "modus": "edit"})


@login_required
def traeger_delete(request, pk):
    traeger = get_object_or_404(Traeger, pk=pk)

    if request.method == "POST":
        confirm_text = request.POST.get("confirm_text")
        if confirm_text == "Löschen":
            traeger.delete()
            messages.success(request, f'Träger erfolgreich gelöscht.')
            return redirect("personal")  # anpassen an deine URL

    return redirect("traeger_detail", pk=traeger.pk)

@login_required
def stellen(request):
    query = request.GET.get("q", "")
    stellens = Stelle.objects.all()
    stellen_anzahl = Stelle.objects.count()

    if query:
        stellens = stellens.filter(
            Q(name__icontains=query) |
            Q(stellen_id__icontains=query) |
            Q(plz__icontains=query) |
            Q(ort__icontains=query)
        )
    ctx = {
        'stellens':stellens,
        'stellen_anzahl':stellen_anzahl,
        "query": query
    }
    return render(request, "stellen/stellen.html", ctx )

@login_required
def stellen_detail(request, pk):
    stellen = get_object_or_404(Stelle, pk=pk)
    return render(request, 'stellen/stellen_detail.html', {'stellen': stellen})

@login_required
def stellen_create(request):
    if request.method == "POST":
        form = StellenForm(request.POST)
        if form.is_valid():
            stelle = form.save(commit=False)
            # Optional: Wenn du ein angelegt_von Feld hast
            # traeger.angelegt_von = request.user
            stelle.save()
            return redirect("stellen")
    else:
        form = StellenForm()

    return render(request, "stellen/stellen_form.html", {"form": form, "modus": "create"})

@login_required
def stellen_edit(request, pk):
    traeger = get_object_or_404(Stelle, pk=pk)

    if request.method == "POST":
        form = StellenForm(request.POST, instance=traeger)
        if form.is_valid():
            form.save()
            return redirect("stellen")  # zurück zur Übersicht
    else:
        form = StellenForm(instance=traeger)

    return render(request, "stellen/stellen_form.html", {"form": form, "modus": "edit"})

@login_required
def stellen_delete(request, pk):
    stelle = get_object_or_404(Stelle, pk=pk)

    if request.method == "POST":
        confirm_text = request.POST.get("confirm_text")
        if confirm_text == "Löschen":
            stelle.delete()
            messages.success(request, f'Stelle erfolgreich gelöscht.')
            return redirect("personal")  # anpassen an deine URL

    return redirect("stellen_detail", pk=stelle.pk)



@login_required
def einrichtung(request):
    query = request.GET.get("q", "")
    einrichtungen = Einrichtung.objects.all()
    einrichtung_anzahl = Einrichtung.objects.count()

    if query:
        einrichtungen = einrichtungen.filter(
            Q(name__icontains=query) |
            Q(einrichtungs_id__icontains=query) |
            Q(einrichtung_art__icontains=query)
        )
    ctx = {
        'einrichtungen': einrichtungen,
        'einrichtung_anzahl': einrichtung_anzahl,
        "query": query
    }
    return render(request, "einrichtung/einrichtung.html", ctx )

@login_required
def einrichtung_detail(request, pk):
    einrichtung = get_object_or_404(Einrichtung, pk=pk)
    return render(request, 'einrichtung/einrichtung_detail.html', {'einrichtung': einrichtung})

@login_required
def einrichtung_create(request):
    if request.method == "POST":
        form = EinrichtungForm(request.POST)
        if form.is_valid():
            einrichtung = form.save(commit=False)
            # Optional: Wenn du ein angelegt_von Feld hast
            # einrichtung.angelegt_von = request.user
            einrichtung.save()
            return redirect("einrichtung")
    else:
        form = EinrichtungForm()

    return render(request, "einrichtung/einrichtung_form.html", {"form": form, "modus": "create"})

@login_required
def einrichtung_edit(request, pk):
    einrichtung = get_object_or_404(Einrichtung, pk=pk)

    if request.method == "POST":
        form = EinrichtungForm(request.POST, instance=einrichtung)
        if form.is_valid():
            form.save()
            return redirect("einrichtung")  # zurück zur Übersicht
    else:
        form = EinrichtungForm(instance=einrichtung)

    return render(request, "einrichtung/einrichtung_form.html", {"form": form, "modus": "edit"})


@login_required
def einrichtung_delete(request, pk):
    einrichtung = get_object_or_404(Einrichtung, pk=pk)

    if request.method == "POST":
        confirm_text = request.POST.get("confirm_text")
        if confirm_text == "Löschen":
            einrichtung.delete()
            messages.success(request, f'Einrichtung erfolgreich gelöscht.')
            return redirect("personal")  # anpassen an deine URL

    return redirect("einrichtung_detail", pk=einrichtung.pk)