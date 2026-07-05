from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now
from django.urls import reverse

from einsatz.models import Einsatz

from .forms import FakturierungsvorgangForm, InnenauftragForm
from .models import Fakturierungsvorgang, Innenauftrag, Quartalsabrechnung


@login_required
def mbw(request):
    today = now().date()
    aktive_einsaetze_qs = Einsatz.objects.filter(aktiv=True).filter(
        Q(ende__isnull=True) | Q(ende__gte=today)
    )
    abrechnung_qs = Einsatz.objects.filter(abrechnung=True)
    freie_innenauftraege_qs = Innenauftrag.objects.filter(einsatz__isnull=True, aktiv=True)
    quartalsabrechnungen_qs = Quartalsabrechnung.objects.filter(jahr=now().year)
    offene_debitoren_qs = Fakturierungsvorgang.objects.filter(
        jahr=now().year
    ).exclude(debitor_status=Fakturierungsvorgang.DebitorStatus.AUSGEGLICHEN)

    context = {
        "aktive_einsaetze_anzahl": aktive_einsaetze_qs.count(),
        "abrechnung_anzahl": abrechnung_qs.count(),
        "offene_abrechnung_anzahl": abrechnung_qs.filter(aktiv=True).count(),
        "freie_innenauftraege_anzahl": freie_innenauftraege_qs.count(),
        "quartalsbuchungen_anzahl": quartalsabrechnungen_qs.count(),
        "offene_debitoren_anzahl": offene_debitoren_qs.count(),
    }
    return render(request, "mbw/mbw.html", context)


@login_required
def aktive_einsaetze(request):
    today = now().date()
    query = request.GET.get("q", "")

    einsaetze = (
        Einsatz.objects.filter(aktiv=True)
        .filter(Q(ende__isnull=True) | Q(ende__gte=today))
        .select_related("stelle", "mitarbeiter")
        .order_by("beginn")
    )

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
    return render(request, "mbw/aktive_einsaetze_list.html", context)


@login_required
def abrechnungsliste(request):
    query = request.GET.get("q", "")
    einsaetze = (
        Einsatz.objects.filter(abrechnung=True)
        .select_related("stelle", "mitarbeiter")
        .order_by("beginn")
    )

    if query:
        einsaetze = einsaetze.filter(
            Q(stelle__name__icontains=query)
            | Q(mitarbeiter__vorname__icontains=query)
            | Q(mitarbeiter__nachname__icontains=query)
            | Q(beginn__icontains=query)
            | Q(ende__icontains=query)
        )

    einsatz_ids = [e.pk for e in einsaetze]
    innenauftraege_map = {
        ia.einsatz_id: ia
        for ia in Innenauftrag.objects.filter(einsatz_id__in=einsatz_ids, aktiv=True).select_related("einsatz")
    }

    abrechnungszeilen = []
    for einsatz in einsaetze:
        abrechnungszeilen.append(
            {"einsatz": einsatz, "innenauftrag": innenauftraege_map.get(einsatz.pk)}
        )

    freie_innenauftraege = Innenauftrag.objects.filter(einsatz__isnull=True, aktiv=True).order_by("nummer")

    context = {
        "abrechnungszeilen": abrechnungszeilen,
        "query": query,
        "einsatz_anzahl": einsaetze.count(),
        "freie_innenauftraege": freie_innenauftraege,
    }
    return render(request, "mbw/abrechnungsliste.html", context)


@login_required
def innenauftraege(request):
    query = request.GET.get("q", "")
    status = request.GET.get("status", "alle")

    innenauftraege_qs = Innenauftrag.objects.select_related(
        "einsatz", "einsatz__stelle", "einsatz__mitarbeiter"
    ).all()

    if query:
        innenauftraege_qs = innenauftraege_qs.filter(
            Q(nummer__icontains=query)
            | Q(bezeichnung__icontains=query)
            | Q(einsatz__stelle__name__icontains=query)
            | Q(einsatz__mitarbeiter__vorname__icontains=query)
            | Q(einsatz__mitarbeiter__nachname__icontains=query)
        )

    if status == "frei":
        innenauftraege_qs = innenauftraege_qs.filter(einsatz__isnull=True)
    elif status == "zugewiesen":
        innenauftraege_qs = innenauftraege_qs.filter(einsatz__isnull=False)

    context = {
        "innenauftraege": innenauftraege_qs.order_by("nummer"),
        "query": query,
        "status": status,
    }
    return render(request, "mbw/innenauftraege.html", context)


@login_required
def innenauftrag_create(request):
    if request.method == "POST":
        form = InnenauftragForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Innenauftrag wurde angelegt.")
            return redirect("innenauftraege")
    else:
        form = InnenauftragForm()

    return render(request, "mbw/innenauftrag_form.html", {"form": form})


@login_required
def innenauftrag_update(request, pk):
    innenauftrag = get_object_or_404(Innenauftrag, pk=pk)

    if request.method == "POST":
        form = InnenauftragForm(request.POST, instance=innenauftrag)
        if form.is_valid():
            form.save()
            messages.success(request, "Innenauftrag wurde aktualisiert.")
            return redirect("innenauftraege")
    else:
        form = InnenauftragForm(instance=innenauftrag)

    return render(
        request,
        "mbw/innenauftrag_form.html",
        {"form": form, "innenauftrag": innenauftrag, "modus": "edit"},
    )


@login_required
def innenauftrag_freigeben(request, pk):
    innenauftrag = get_object_or_404(Innenauftrag, pk=pk)
    if request.method == "POST":
        innenauftrag.einsatz = None
        innenauftrag.andock_art = ""
        innenauftrag.save(update_fields=["einsatz", "andock_art", "aktualisiert_am"])
        messages.success(request, f"Innenauftrag {innenauftrag.nummer} ist wieder frei.")
    return redirect("innenauftraege")


@login_required
def innenauftrag_zuweisen(request, pk):
    einsatz = get_object_or_404(Einsatz.objects.select_related("stelle", "mitarbeiter"), pk=pk)

    if request.method != "POST":
        return redirect("abrechnungsliste")

    innenauftrag_id = request.POST.get("innenauftrag_id")
    andock = request.POST.get("andock")

    if not innenauftrag_id:
        messages.error(request, "Bitte einen freien Innenauftrag auswählen.")
        return redirect("abrechnungsliste")

    innenauftrag = get_object_or_404(Innenauftrag, pk=innenauftrag_id, aktiv=True)

    if not innenauftrag.ist_frei:
        messages.error(request, "Der ausgewählte Innenauftrag ist nicht mehr frei.")
        return redirect("abrechnungsliste")

    if andock not in {Innenauftrag.AndockArt.STELLE, Innenauftrag.AndockArt.PERSON}:
        messages.error(request, "Ungültige Zuordnungsart.")
        return redirect("abrechnungsliste")

    if Innenauftrag.objects.filter(einsatz=einsatz).exists():
        messages.error(request, "Dieser Einsatz hat bereits einen Innenauftrag.")
        return redirect("abrechnungsliste")

    try:
        innenauftrag.einsatz = einsatz
        innenauftrag.andock_art = andock
        innenauftrag.full_clean()
        innenauftrag.save()
    except Exception as exc:
        messages.error(request, f"Zuordnung fehlgeschlagen: {exc}")
        return redirect("abrechnungsliste")

    messages.success(request, f"Innenauftrag {innenauftrag.nummer} wurde zugeordnet.")
    return redirect("abrechnungsliste")


@login_required
def quartalsuebersicht(request):
    current_year = now().year
    query = request.GET.get("q", "")
    jahr_raw = request.GET.get("jahr", str(current_year))

    try:
        jahr = int(jahr_raw)
    except ValueError:
        jahr = current_year

    einsaetze = (
        Einsatz.objects.filter(abrechnung=True)
        .select_related("stelle", "mitarbeiter", "innenauftrag")
        .order_by("mitarbeiter__nachname", "mitarbeiter__vorname")
    )

    if query:
        einsaetze = einsaetze.filter(
            Q(stelle__name__icontains=query)
            | Q(mitarbeiter__vorname__icontains=query)
            | Q(mitarbeiter__nachname__icontains=query)
            | Q(innenauftrag__nummer__icontains=query)
        )

    einsatz_ids = [e.pk for e in einsaetze]
    quartalsdaten = Quartalsabrechnung.objects.filter(jahr=jahr, einsatz_id__in=einsatz_ids)
    quartal_map = {(q.einsatz_id, q.quartal): q for q in quartalsdaten}

    zeilen = []
    for einsatz in einsaetze:
        zeilen.append(
            {
                "einsatz": einsatz,
                "q1": quartal_map.get((einsatz.pk, 1)),
                "q2": quartal_map.get((einsatz.pk, 2)),
                "q3": quartal_map.get((einsatz.pk, 3)),
                "q4": quartal_map.get((einsatz.pk, 4)),
            }
        )

    jahre = [current_year - 1, current_year, current_year + 1]
    context = {
        "zeilen": zeilen,
        "jahr": jahr,
        "jahre": jahre,
        "query": query,
    }
    return render(request, "mbw/quartalsuebersicht.html", context)


@login_required
def quartalsabrechnung_buchen(request, pk):
    einsatz = get_object_or_404(Einsatz, pk=pk, abrechnung=True)
    if request.method != "POST":
        return redirect("quartalsuebersicht")

    jahr_raw = request.POST.get("jahr")
    quartal_raw = request.POST.get("quartal")

    try:
        jahr = int(jahr_raw)
        quartal = int(quartal_raw)
    except (TypeError, ValueError):
        messages.error(request, "Ungültige Angaben für Jahr oder Quartal.")
        return redirect("quartalsuebersicht")

    if quartal not in {1, 2, 3, 4}:
        messages.error(request, "Quartal muss zwischen 1 und 4 liegen.")
        return redirect("quartalsuebersicht")

    if Quartalsabrechnung.objects.filter(einsatz=einsatz, jahr=jahr, quartal=quartal).exists():
        messages.warning(request, "Dieses Quartal ist für den Einsatz bereits verbucht.")
    else:
        eintrag = Quartalsabrechnung.objects.create(
            einsatz=einsatz,
            jahr=jahr,
            quartal=quartal,
        )
        messages.success(
            request,
            f"Q{quartal} ({eintrag.get_art_display()}) für {einsatz.mitarbeiter} wurde verbucht.",
        )

    return redirect(f"{reverse('quartalsuebersicht')}?jahr={jahr}")


@login_required
def fakturierungsliste(request):
    current_year = now().year
    query = request.GET.get("q", "")
    jahr_raw = request.GET.get("jahr", str(current_year))

    try:
        jahr = int(jahr_raw)
    except ValueError:
        jahr = current_year

    einsaetze = (
        Einsatz.objects.filter(abrechnung=True)
        .select_related("stelle", "mitarbeiter", "innenauftrag")
        .order_by("mitarbeiter__nachname", "mitarbeiter__vorname")
    )

    if query:
        einsaetze = einsaetze.filter(
            Q(stelle__name__icontains=query)
            | Q(mitarbeiter__vorname__icontains=query)
            | Q(mitarbeiter__nachname__icontains=query)
            | Q(innenauftrag__nummer__icontains=query)
        )

    einsatz_ids = [e.pk for e in einsaetze]
    vorgaenge = Fakturierungsvorgang.objects.filter(jahr=jahr, einsatz_id__in=einsatz_ids)
    vorgang_map = {v.einsatz_id: v for v in vorgaenge}

    zeilen = [{"einsatz": e, "vorgang": vorgang_map.get(e.pk)} for e in einsaetze]

    offene_debitoren = vorgaenge.exclude(
        debitor_status=Fakturierungsvorgang.DebitorStatus.AUSGEGLICHEN
    ).count()

    context = {
        "zeilen": zeilen,
        "jahr": jahr,
        "jahre": [current_year - 1, current_year, current_year + 1],
        "query": query,
        "offene_debitoren": offene_debitoren,
    }
    return render(request, "mbw/fakturierungsliste.html", context)


@login_required
def fakturierung_bearbeiten(request, pk):
    einsatz = get_object_or_404(
        Einsatz.objects.select_related("stelle", "mitarbeiter", "innenauftrag"),
        pk=pk,
        abrechnung=True,
    )

    current_year = now().year
    jahr_raw = request.GET.get("jahr") if request.method == "GET" else request.POST.get("jahr")
    try:
        jahr = int(jahr_raw) if jahr_raw else current_year
    except ValueError:
        jahr = current_year

    vorgang, _ = Fakturierungsvorgang.objects.get_or_create(
        einsatz=einsatz,
        jahr=jahr,
        defaults={"debitor_status": Fakturierungsvorgang.DebitorStatus.OFFEN},
    )

    if request.method == "POST":
        form = FakturierungsvorgangForm(request.POST, request.FILES, instance=vorgang)
        if form.is_valid():
            form.save()
            messages.success(request, "Fakturierungsvorgang wurde gespeichert.")
            return redirect(f"{reverse('fakturierungsliste')}?jahr={jahr}")
    else:
        form = FakturierungsvorgangForm(instance=vorgang)

    context = {
        "form": form,
        "einsatz": einsatz,
        "jahr": jahr,
        "vorgang": vorgang,
    }
    return render(request, "mbw/fakturierung_form.html", context)
