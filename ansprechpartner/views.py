from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from .forms import AnsprechForm
from .models import Ansprechpartner


@login_required
def ansprech(request):
    query = request.GET.get("q", "")
    ansprechpartners = Ansprechpartner.objects.all()
    ansprechpartner_anzahl = Ansprechpartner.objects.count()

    if query:
        ansprechpartners = ansprechpartners.filter(
            Q(personalnummer__icontains=query) |
            Q(vorname__icontains=query) |
            Q(nachname__icontains=query)
        )

    ctx = {
        'ansprechpartners':ansprechpartners,
        'ansprechpartner_anzahl':ansprechpartner_anzahl,
        "query": query
    }
    return render(request, "ansprechpartner/ansprechpartner.html", ctx )

@login_required
def ansprech_detail(request, pk):
    ansprechpartner = get_object_or_404(Ansprechpartner, pk=pk)
    return render(request, 'ansprechpartner/ansprech_detail.html', {'ansprechpartner': ansprechpartner})

@login_required
def ansprech_create(request):
    if request.method == "POST":
        form = AnsprechForm(request.POST)
        if form.is_valid():
            ansprechpartner = form.save(commit=False)
            ansprechpartner.angelegt_von = request.user
            ansprechpartner.save()
            return redirect("ansprech_detail", pk=ansprechpartner.pk)
    else:
        form = AnsprechForm()

    return render(request, "ansprechpartner/ansprech_form.html", {"form": form})

@login_required
def ansprech_update(request, pk):
    ansprechpartner = get_object_or_404(Ansprechpartner, pk=pk)

    if request.method == "POST":
        form = AnsprechForm(request.POST, instance=ansprechpartner)
        if form.is_valid():
            form.save()
            return redirect("ansprech_detail", pk=ansprechpartner.pk)
    else:
        form = AnsprechForm(instance=ansprechpartner)

    return render(request, "ansprechpartner/ansprech_form.html", {
        "form": form,
        "ansprechpartner": ansprechpartner,
        "modus": "edit"
    })

@login_required
def ansprech_delete(request, pk):
    ansprechpartner = get_object_or_404(Ansprechpartner, pk=pk)

    if request.method == "POST":
        confirm_text = request.POST.get("confirm_text")
        if confirm_text == "Löschen":
            ansprechpartner.delete()
            messages.success(request, f'Ansprechpartner*in erfolgreich gelöscht.')
            return redirect("ansprech")  # anpassen an deine URL

    return redirect("ansprech_detail", pk=ansprechpartner.pk)



