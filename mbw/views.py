from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.timezone import now
from django.urls import reverse

from einsatz.models import Einsatz

from . import kalkulation, services
from .forms import (
    DebitorForm,
    FakturierungsvorgangForm,
    InnenauftragForm,
    TabellenErhoehungForm,
    ZahlungseingangForm,
)
from .models import (
    BESOLDUNGSGRUPPEN,
    Beihilfesatz,
    Besoldungstabelle,
    Debitor,
    Fakturierungsvorgang,
    Familienzuschlagtabelle,
    Innenauftrag,
    Mietenstufe,
    Quartalsabrechnung,
    Zulagensatz,
)


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
        "einsatz", "einsatz__stelle", "einsatz__mitarbeiter", "debitor"
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
@permission_required("mbw.add_innenauftrag", raise_exception=True)
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
@permission_required("mbw.change_innenauftrag", raise_exception=True)
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
@permission_required("mbw.change_innenauftrag", raise_exception=True)
def innenauftrag_freigeben(request, pk):
    innenauftrag = get_object_or_404(Innenauftrag, pk=pk)
    if request.method == "POST":
        innenauftrag.einsatz = None
        innenauftrag.andock_art = ""
        innenauftrag.save(update_fields=["einsatz", "andock_art", "aktualisiert_am"])
        messages.success(request, f"Innenauftrag {innenauftrag.nummer} ist wieder frei.")
    return redirect("innenauftraege")


@login_required
@permission_required("mbw.change_innenauftrag", raise_exception=True)
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
@permission_required("mbw.add_quartalsabrechnung", raise_exception=True)
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

    betrag = None
    betrag_raw = (request.POST.get("betrag") or "").replace(",", ".").strip()
    if betrag_raw:
        try:
            betrag = Decimal(betrag_raw)
        except InvalidOperation:
            messages.error(request, "Ungültiger Betrag.")
            return redirect(f"{reverse('quartalsuebersicht')}?jahr={jahr}")

    if Quartalsabrechnung.objects.filter(einsatz=einsatz, jahr=jahr, quartal=quartal).exists():
        messages.warning(request, "Dieses Quartal ist für den Einsatz bereits verbucht.")
    else:
        eintrag = Quartalsabrechnung.objects.create(
            einsatz=einsatz,
            jahr=jahr,
            quartal=quartal,
            betrag=betrag,
        )
        messages.success(
            request,
            f"Q{quartal} ({eintrag.get_art_display()}) für {einsatz.mitarbeiter} wurde verbucht.",
        )
        # Forderung hat sich geändert → Debitor-Status neu ableiten (falls Akte existiert)
        vorgang = Fakturierungsvorgang.objects.filter(einsatz=einsatz, jahr=jahr).first()
        if vorgang:
            vorgang.debitor_status_aktualisieren()

    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
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
@permission_required("mbw.change_fakturierungsvorgang", raise_exception=True)
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


# --- Stammdaten -------------------------------------------------------------


@login_required
def stammdaten(request):
    context = {
        "besoldungstabellen": Besoldungstabelle.objects.all(),
        "fz_tabellen": Familienzuschlagtabelle.objects.all(),
        "beihilfe_jahre": (
            Beihilfesatz.objects.values_list("jahr", flat=True).distinct().order_by("-jahr")
        ),
        "zulagen": Zulagensatz.objects.order_by("art", "variante", "-gueltig_ab"),
        "mietenstufen_anzahl": Mietenstufe.objects.count(),
        "debitoren_anzahl": Debitor.objects.filter(aktiv=True).count(),
        "besoldung_form": TabellenErhoehungForm(prefix="besoldung"),
        "fz_form": TabellenErhoehungForm(prefix="fz"),
    }
    return render(request, "mbw/stammdaten.html", context)


def _besoldung_stufen(vorlage, request):
    """Stufen-Spalten des Rasters: beim Speichern aus dem Formular, sonst aus der Vorlage."""
    if request.method == "POST" and request.POST.get("stufen"):
        return [int(s) for s in request.POST["stufen"].split(",") if s.strip().isdigit()]
    vorhandene = sorted({b.stufe for b in vorlage.betraege.all()}) if vorlage else []
    max_stufe = max(vorhandene) if vorhandene else 8
    return list(range(1, max_stufe + 1))


def _besoldungstabelle_bearbeiten(request, tabelle, vorlage):
    from datetime import date as _date

    from django.core.exceptions import PermissionDenied

    stufen = _besoldung_stufen(vorlage, request)

    if request.method == "POST":
        perm = "mbw.change_besoldungstabelle" if tabelle else "mbw.add_besoldungstabelle"
        if not request.user.has_perm(perm):
            raise PermissionDenied

        try:
            gueltig_ab = _date.fromisoformat(request.POST.get("gueltig_ab", ""))
        except ValueError:
            gueltig_ab = None
        bemerkung = request.POST.get("bemerkung", "").strip()

        try:
            betrag_map = {
                (gruppe, stufe): services.betrag_parsen(request.POST.get(f"b_{gruppe}_{stufe}", ""))
                for gruppe, _ in BESOLDUNGSGRUPPEN
                for stufe in stufen
            }
            tabelle = services.besoldungstabelle_speichern(tabelle, gueltig_ab, bemerkung, betrag_map)
        except ValueError as fehler:
            messages.error(request, str(fehler))
        else:
            messages.success(request, f"{tabelle} gespeichert.")
            return redirect("besoldungstabelle_detail", pk=tabelle.pk)

    quelle = tabelle or vorlage
    matrix = {}
    if quelle:
        for betrag in quelle.betraege.all():
            matrix.setdefault(betrag.gruppe, {})[betrag.stufe] = betrag.betrag
    zeilen = [
        {"gruppe": gruppe, "werte": [(stufe, matrix.get(gruppe, {}).get(stufe)) for stufe in stufen]}
        for gruppe, _ in BESOLDUNGSGRUPPEN
    ]
    context = {
        "tabelle": tabelle,
        "stufen": stufen,
        "stufen_csv": ",".join(str(s) for s in stufen),
        "zeilen": zeilen,
        "ist_neu": tabelle is None,
        "kann_bearbeiten": request.user.has_perm(
            "mbw.change_besoldungstabelle" if tabelle else "mbw.add_besoldungstabelle"
        ),
    }
    return render(request, "mbw/besoldungstabelle_detail.html", context)


@login_required
def besoldungstabelle_detail(request, pk):
    from .models import Besoldungstabelle as _Bt

    tabelle = get_object_or_404(_Bt, pk=pk)
    return _besoldungstabelle_bearbeiten(request, tabelle, vorlage=tabelle)


@login_required
@permission_required("mbw.add_besoldungstabelle", raise_exception=True)
def besoldungstabelle_neu(request):
    vorlage = Besoldungstabelle.objects.order_by("-gueltig_ab").first()
    return _besoldungstabelle_bearbeiten(request, None, vorlage=vorlage)


@login_required
@permission_required("mbw.add_besoldungstabelle", raise_exception=True)
def besoldungstabelle_erhoehen(request):
    if request.method != "POST":
        return redirect("mbw_stammdaten")
    form = TabellenErhoehungForm(request.POST, prefix="besoldung")
    if form.is_valid():
        try:
            tabelle = services.besoldungstabelle_fortschreiben(
                form.cleaned_data["gueltig_ab"], form.cleaned_data["prozent"]
            )
            messages.success(request, f"{tabelle} angelegt.")
        except ValueError as fehler:
            messages.error(request, str(fehler))
    else:
        messages.error(request, "Bitte Datum und Prozentsatz prüfen.")
    return redirect("mbw_stammdaten")


FZ_FELDER = [
    ("stufe_l", "Stufe L"), ("stufe_v", "Stufe V"),
    ("stufe_1", "Stufe 1"), ("stufe_2", "Stufe 2"),
    ("kind_3", "3. Kind"), ("kind_weitere", "je weit. Kind"),
]
FZ_KINDER_GRUPPEN = ["A8", "A9", "A10"]


def _fz_tabelle_bearbeiten(request, tabelle, vorlage):
    from datetime import date as _date

    from django.core.exceptions import PermissionDenied

    from .models import ORTSKLASSEN

    ortsklassen = list(ORTSKLASSEN.choices)

    if request.method == "POST":
        perm = "mbw.change_familienzuschlagtabelle" if tabelle else "mbw.add_familienzuschlagtabelle"
        if not request.user.has_perm(perm):
            raise PermissionDenied

        try:
            gueltig_ab = _date.fromisoformat(request.POST.get("gueltig_ab", ""))
        except ValueError:
            gueltig_ab = None
        bemerkung = request.POST.get("bemerkung", "").strip()

        try:
            zeilen_map = {
                wert: {
                    feld: services.betrag_parsen(request.POST.get(f"z_{wert}_{feld}", ""))
                    for feld, _ in FZ_FELDER
                }
                for wert, _ in ortsklassen
            }
            kinder_map = {
                (gruppe, wert): services.betrag_parsen(request.POST.get(f"k_{gruppe}_{wert}", ""))
                for gruppe in FZ_KINDER_GRUPPEN
                for wert, _ in ortsklassen
            }
            tabelle = services.fz_tabelle_speichern(
                tabelle, gueltig_ab, bemerkung, zeilen_map, kinder_map
            )
        except ValueError as fehler:
            messages.error(request, str(fehler))
        else:
            messages.success(request, f"{tabelle} gespeichert.")
            return redirect("fz_tabelle_detail", pk=tabelle.pk)

    quelle = tabelle or vorlage
    zeilen_werte = {z.ortsklasse: z for z in quelle.zeilen.all()} if quelle else {}
    kinder_werte = {
        (k.gruppe, k.ortsklasse): k.betrag for k in quelle.kinder_erhoehungen.all()
    } if quelle else {}

    zeilen = [
        {
            "wert": wert, "label": label,
            "zellen": [
                (feld, getattr(zeilen_werte.get(wert), feld, None))
                for feld, _ in FZ_FELDER
            ],
        }
        for wert, label in ortsklassen
    ]
    kinder = [
        {"gruppe": gruppe, "zellen": [(wert, kinder_werte.get((gruppe, wert))) for wert, _ in ortsklassen]}
        for gruppe in FZ_KINDER_GRUPPEN
    ]

    context = {
        "tabelle": tabelle,
        "felder": FZ_FELDER,
        "ortsklassen": ortsklassen,
        "zeilen": zeilen,
        "kinder": kinder,
        "ist_neu": tabelle is None,
        "kann_bearbeiten": request.user.has_perm(
            "mbw.change_familienzuschlagtabelle" if tabelle else "mbw.add_familienzuschlagtabelle"
        ),
    }
    return render(request, "mbw/fz_tabelle_detail.html", context)


@login_required
def fz_tabelle_detail(request, pk):
    tabelle = get_object_or_404(Familienzuschlagtabelle, pk=pk)
    return _fz_tabelle_bearbeiten(request, tabelle, vorlage=tabelle)


@login_required
@permission_required("mbw.add_familienzuschlagtabelle", raise_exception=True)
def fz_tabelle_neu(request):
    vorlage = Familienzuschlagtabelle.objects.order_by("-gueltig_ab").first()
    return _fz_tabelle_bearbeiten(request, None, vorlage=vorlage)


@login_required
@permission_required("mbw.add_familienzuschlagtabelle", raise_exception=True)
def fz_tabelle_erhoehen(request):
    if request.method != "POST":
        return redirect("mbw_stammdaten")
    form = TabellenErhoehungForm(request.POST, prefix="fz")
    if form.is_valid():
        try:
            tabelle = services.fz_tabelle_fortschreiben(
                form.cleaned_data["gueltig_ab"], form.cleaned_data["prozent"]
            )
            messages.success(request, f"{tabelle} angelegt.")
        except ValueError as fehler:
            messages.error(request, str(fehler))
    else:
        messages.error(request, "Bitte Datum und Prozentsatz prüfen.")
    return redirect("mbw_stammdaten")


@login_required
def debitorenliste(request):
    query = request.GET.get("q", "")
    debitoren = Debitor.objects.select_related("traeger").all()
    if query:
        debitoren = debitoren.filter(
            Q(name__icontains=query)
            | Q(name2__icontains=query)
            | Q(sap_nummer__icontains=query)
            | Q(ort__icontains=query)
            | Q(traeger__name__icontains=query)
        )
    context = {"debitoren": debitoren, "query": query}
    return render(request, "mbw/debitorenliste.html", context)


@login_required
@permission_required("mbw.add_debitor", raise_exception=True)
def debitor_create(request):
    if request.method == "POST":
        form = DebitorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Debitor wurde angelegt.")
            return redirect("debitorenliste")
    else:
        form = DebitorForm()
    return render(request, "mbw/debitor_form.html", {"form": form})


@login_required
@permission_required("mbw.change_debitor", raise_exception=True)
def debitor_update(request, pk):
    debitor = get_object_or_404(Debitor, pk=pk)
    if request.method == "POST":
        form = DebitorForm(request.POST, instance=debitor)
        if form.is_valid():
            form.save()
            messages.success(request, "Debitor wurde aktualisiert.")
            return redirect("debitorenliste")
    else:
        form = DebitorForm(instance=debitor)
    return render(
        request, "mbw/debitor_form.html", {"form": form, "debitor": debitor, "modus": "edit"}
    )


@login_required
def mietenstufen(request):
    query = request.GET.get("q", "")
    stufen = Mietenstufe.objects.all()
    if query:
        stufen = stufen.filter(name__icontains=query)
    context = {"mietenstufen": stufen[:100], "query": query, "anzahl": stufen.count()}
    return render(request, "mbw/mietenstufen.html", context)


# --- Jahresakte -------------------------------------------------------------


def _einsatz_fuer_jahresakte(pk):
    return get_object_or_404(
        Einsatz.objects.select_related(
            "stelle", "stelle__einrichtung", "stelle__einrichtung__traeger", "mitarbeiter"
        ),
        pk=pk,
        abrechnung=True,
    )


def _rechnungstext(einsatz, vorgang, innenauftrag, debitor, jahr, quartal):
    from django.template.loader import render_to_string

    return render_to_string(
        "mbw/rechnungstext_abschlag.txt",
        {
            "einsatz": einsatz,
            "mitarbeiter": einsatz.mitarbeiter,
            "stelle": einsatz.stelle,
            "einrichtung": einsatz.stelle.einrichtung,
            "titel": einsatz.mitarbeiter.get_diakon_titel(),
            "innenauftrag": innenauftrag,
            "debitor": debitor,
            "jahr": jahr,
            "quartal": quartal,
            "abschlag": vorgang.abschlag_quartal,
            "hochrechnung": vorgang.hochrechnung_gesamt,
        },
    ).strip()


@login_required
def jahresakte(request, pk, jahr):
    einsatz = _einsatz_fuer_jahresakte(pk)
    vorgang = Fakturierungsvorgang.objects.filter(einsatz=einsatz, jahr=jahr).select_related("debitor").first()
    innenauftrag = Innenauftrag.objects.filter(einsatz=einsatz).select_related("debitor").first()
    debitor = (vorgang.debitor if vorgang else None) or (innenauftrag.debitor if innenauftrag else None)

    quartal_map = {
        q.quartal: q for q in Quartalsabrechnung.objects.filter(einsatz=einsatz, jahr=jahr)
    }
    quartale = [
        {"nr": nr, "eintrag": quartal_map.get(nr), "ist_spitze": nr == 4}
        for nr in (1, 2, 3, 4)
    ]

    rechnungstexte = []
    if vorgang and vorgang.abschlag_quartal:
        rechnungstexte = [
            {"quartal": nr, "text": _rechnungstext(einsatz, vorgang, innenauftrag, debitor, jahr, nr)}
            for nr in (1, 2, 3)
        ]

    spitze = _spitze_vorschlag(einsatz, int(jahr), vorgang)
    spitze_text = None
    if vorgang and vorgang.spitze_rest is not None and not spitze.get("fehlt"):
        from django.template.loader import render_to_string

        spitze_text = render_to_string(
            "mbw/rechnungstext_spitze.txt",
            {
                "einsatz": einsatz,
                "mitarbeiter": einsatz.mitarbeiter,
                "stelle": einsatz.stelle,
                "einrichtung": einsatz.stelle.einrichtung,
                "titel": einsatz.mitarbeiter.get_diakon_titel(),
                "innenauftrag": innenauftrag,
                "debitor": debitor,
                "jahr": int(jahr),
                "vorgang": vorgang,
                "spitze": spitze,
            },
        ).strip()

    zahlungen = list(vorgang.zahlungseingaenge.all()) if vorgang else []

    context = {
        "einsatz": einsatz,
        "jahr": int(jahr),
        "vorgang": vorgang,
        "innenauftrag": innenauftrag,
        "debitor": debitor,
        "quartale": quartale,
        "kalkulation": vorgang.kalkulation if vorgang else None,
        "rechnungstexte": rechnungstexte,
        "spitze": spitze,
        "spitze_text": spitze_text,
        "zahlungen": zahlungen,
        "zahlung_form": ZahlungseingangForm(),
        "forderung_gesamt": vorgang.forderung_gesamt if vorgang else None,
        "bezahlt_summe": vorgang.bezahlt_summe if vorgang else Decimal("0"),
        "offener_betrag": vorgang.offener_betrag if vorgang else None,
    }
    return render(request, "mbw/jahresakte.html", context)


@login_required
@permission_required("mbw.add_zahlungseingang", raise_exception=True)
def zahlungseingang_anlegen(request, pk, jahr):
    einsatz = _einsatz_fuer_jahresakte(pk)
    if request.method != "POST":
        return redirect("jahresakte", pk=pk, jahr=jahr)

    vorgang, _ = Fakturierungsvorgang.objects.get_or_create(einsatz=einsatz, jahr=jahr)
    form = ZahlungseingangForm(request.POST)
    if form.is_valid():
        zahlung = form.save(commit=False)
        zahlung.vorgang = vorgang
        zahlung.erfasst_von = request.user
        zahlung.save()
        vorgang.debitor_status_aktualisieren()
        messages.success(
            request,
            f"Zahlungseingang {zahlung.betrag} € vom {zahlung.datum:%d.%m.%Y} erfasst.",
        )
    else:
        for feld, fehler in form.errors.items():
            messages.error(request, f"{feld}: {', '.join(fehler)}")
    return redirect("jahresakte", pk=pk, jahr=jahr)


@login_required
@permission_required("mbw.delete_zahlungseingang", raise_exception=True)
def zahlungseingang_loeschen(request, pk):
    from .models import Zahlungseingang

    zahlung = get_object_or_404(
        Zahlungseingang.objects.select_related("vorgang"), pk=pk
    )
    vorgang = zahlung.vorgang
    einsatz_pk, jahr = vorgang.einsatz_id, vorgang.jahr
    if request.method == "POST":
        zahlung.delete()
        vorgang.debitor_status_aktualisieren()
        messages.success(request, "Zahlungseingang gelöscht.")
    return redirect("jahresakte", pk=einsatz_pk, jahr=jahr)


@login_required
@permission_required("mbw.change_fakturierungsvorgang", raise_exception=True)
def jahresakte_kalkulieren(request, pk, jahr):
    einsatz = _einsatz_fuer_jahresakte(pk)
    if request.method != "POST":
        return redirect("jahresakte", pk=pk, jahr=jahr)

    try:
        ergebnis = kalkulation.hochrechnung_berechnen(einsatz, int(jahr))
    except kalkulation.KalkulationsFehler as fehler:
        for meldung in fehler.args[0]:
            messages.error(request, meldung)
        return redirect("jahresakte", pk=pk, jahr=jahr)

    vorgang, _ = Fakturierungsvorgang.objects.get_or_create(einsatz=einsatz, jahr=jahr)
    gesamt = ergebnis["summen"]["gesamt"]
    vorgang.kalkulation = {
        "eingaben": ergebnis["eingaben"],
        "monate": ergebnis["monate"],
        "summen": {name: str(wert) for name, wert in ergebnis["summen"].items()},
    }
    vorgang.hochrechnung_gesamt = gesamt
    vorgang.abschlag_quartal = kalkulation.abschlag_vorschlag(gesamt)
    vorgang.kalkuliert_am = now()
    if vorgang.debitor is None:
        innenauftrag = Innenauftrag.objects.filter(einsatz=einsatz).first()
        if innenauftrag and innenauftrag.debitor:
            vorgang.debitor = innenauftrag.debitor
    vorgang.save()

    messages.success(
        request,
        f"Hochrechnung {jahr}: {gesamt} € gesamt, Abschlag {vorgang.abschlag_quartal} € je Quartal.",
    )
    return redirect("jahresakte", pk=pk, jahr=jahr)


# --- Personalkosten-Import (SAP) --------------------------------------------


@login_required
def pk_import_liste(request):
    from django.core.exceptions import PermissionDenied

    from . import sap_import
    from .forms import PKImportForm
    from .models import PersonalkostenImport

    if request.method == "POST":
        if not request.user.has_perm("mbw.add_personalkostenimport"):
            raise PermissionDenied
        form = PKImportForm(request.POST, request.FILES)
        if form.is_valid():
            datei = form.cleaned_data["datei"]
            try:
                lauf, statistik = sap_import.sap_import_anlegen(
                    datei.read(),
                    datei.name,
                    benutzer=request.user,
                    bemerkung=form.cleaned_data["bemerkung"],
                )
            except sap_import.SapImportFehler as fehler:
                messages.error(request, f"Import fehlgeschlagen: {fehler}")
            else:
                messages.success(
                    request,
                    f"{statistik['zeilen']} Zeilen eingelesen, "
                    f"{statistik['storno_paare']} Storno-Paare erkannt.",
                )
                return redirect("pk_import_detail", pk=lauf.pk)
    else:
        form = PKImportForm()

    importe = PersonalkostenImport.objects.select_related("hochgeladen_von").all()
    context = {"importe": importe, "form": form}
    return render(request, "mbw/pk_import_liste.html", context)


@login_required
def pk_import_detail(request, pk):
    from . import sap_import
    from .models import PersonalkostenImport

    import_lauf = get_object_or_404(PersonalkostenImport, pk=pk)
    faelle = sap_import.faelle(import_lauf)

    fuer_jahresakte = {}
    for fall in faelle:
        if fall["einsatz"]:
            fuer_jahresakte[fall["auftrag_nummer"]] = fall["einsatz"].pk

    ohne_innenauftrag = [fall for fall in faelle if fall["innenauftrag"] is None]
    ohne_einsatz = [fall for fall in faelle if fall["innenauftrag"] and fall["einsatz"] is None]

    debitoren = {}
    for fall in faelle:
        if fall["debitor"]:
            debitoren.setdefault(fall["debitor"].pk, {"debitor": fall["debitor"], "anzahl": 0})
            debitoren[fall["debitor"].pk]["anzahl"] += 1

    context = {
        "import_lauf": import_lauf,
        "faelle": faelle,
        "zeilen_anzahl": import_lauf.zeilen.count(),
        "storno_anzahl": import_lauf.zeilen.filter(storno_partner__isnull=False).count() // 2,
        "ohne_innenauftrag": ohne_innenauftrag,
        "ohne_einsatz": ohne_einsatz,
        "debitoren": [wert for wert in debitoren.values() if wert["anzahl"] > 1],
    }
    return render(request, "mbw/pk_import_detail.html", context)


@login_required
@permission_required("mbw.delete_personalkostenimport", raise_exception=True)
def pk_import_loeschen(request, pk):
    from .models import PersonalkostenImport

    import_lauf = get_object_or_404(PersonalkostenImport, pk=pk)
    if request.method == "POST":
        name = str(import_lauf)
        import_lauf.delete()
        messages.success(request, f"Import „{name}“ wurde gelöscht.")
    return redirect("pk_import_liste")


@login_required
def pk_fall_excel(request, pk, personalnummer, auftrag):
    from django.http import HttpResponse

    from . import fall_export, sap_import
    from .models import PersonalkostenImport

    import_lauf = get_object_or_404(PersonalkostenImport, pk=pk)
    fall = next(
        (f for f in sap_import.faelle(import_lauf)
         if f["personalnummer"] == personalnummer and f["auftrag_nummer"] == auftrag),
        None,
    )
    if fall is None:
        messages.error(request, "Fall nicht im Import gefunden.")
        return redirect("pk_import_detail", pk=pk)

    puffer = fall_export.einzel_mappe(import_lauf, fall)
    dateiname = f"{fall['nachname']}_{fall['vorname']}_{fall['personalnummer']}_{import_lauf.jahr}.xlsx"
    antwort = HttpResponse(
        puffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    antwort["Content-Disposition"] = f'attachment; filename="{dateiname}"'
    return antwort


@login_required
def pk_debitor_mappe(request, pk, debitor_pk):
    from django.http import HttpResponse

    from . import fall_export, sap_import
    from .models import PersonalkostenImport

    import_lauf = get_object_or_404(PersonalkostenImport, pk=pk)
    debitor = get_object_or_404(Debitor, pk=debitor_pk)
    faelle = [
        fall for fall in sap_import.faelle(import_lauf)
        if fall["debitor"] and fall["debitor"].pk == debitor.pk
    ]
    if not faelle:
        messages.error(request, "Keine Fälle für diesen Debitor im Import.")
        return redirect("pk_import_detail", pk=pk)

    puffer = fall_export.debitor_mappe(import_lauf, debitor, faelle)
    dateiname = f"PK-Abrechnung_{import_lauf.jahr}_Debitor_{debitor.sap_nummer or debitor.pk}.xlsx"
    antwort = HttpResponse(
        puffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    antwort["Content-Disposition"] = f'attachment; filename="{dateiname}"'
    return antwort


# --- Spitzabrechnung ---------------------------------------------------------


def _spitze_vorschlag(einsatz, jahr, vorgang):
    """Ist-Positionen aus dem jüngsten Import des Jahres + Kalkulations-Beihilfe."""
    from django.db.models import Sum

    from .models import PersonalkostenImport

    innenauftrag = Innenauftrag.objects.filter(einsatz=einsatz).first()
    if innenauftrag is None:
        return {"fehlt": "Kein Innenauftrag zugeordnet."}
    import_lauf = PersonalkostenImport.objects.filter(jahr=jahr).first()
    if import_lauf is None:
        return {"fehlt": f"Noch kein Personalkosten-Import für {jahr} vorhanden."}

    zeilen = import_lauf.zeilen.filter(
        auftrag_nummer=innenauftrag.nummer,
        personalnummer=einsatz.mitarbeiter.personalnummer,
    )
    if not zeilen.exists():
        return {
            "fehlt": f"Import „{import_lauf.dateiname}“ enthält keine Zeilen zu "
                     f"IA {innenauftrag.nummer} / PersNr {einsatz.mitarbeiter.personalnummer}.",
            "import_lauf": import_lauf,
        }

    def konto_summe(konto):
        return zeilen.filter(hauptbuchkonto=konto).aggregate(s=Sum("betrag"))["s"] or Decimal("0")

    bezuege = konto_summe("603100")
    umlage = konto_summe("609800")

    beihilfe = kv = None
    if vorgang and vorgang.kalkulation:
        beihilfe = Decimal(vorgang.kalkulation["summen"]["beihilfe"])
        kv = Decimal(vorgang.kalkulation["summen"]["kv_zuschuss"])
    pos_beihilfe = (beihilfe or Decimal("0")) + (kv or Decimal("0"))

    abschlaege = list(
        Quartalsabrechnung.objects.filter(einsatz=einsatz, jahr=jahr, quartal__lte=3).order_by("quartal")
    )
    abschlag_summe = sum((a.betrag or Decimal("0") for a in abschlaege), Decimal("0"))
    pk_gesamt = bezuege + umlage + pos_beihilfe

    return {
        "import_lauf": import_lauf,
        "innenauftrag": innenauftrag,
        "bezuege": bezuege,
        "umlage": umlage,
        "beihilfe": beihilfe,
        "kv": kv,
        "pos_beihilfe": pos_beihilfe,
        "pk_gesamt": pk_gesamt,
        "abschlaege": abschlaege,
        "abschlag_summe": abschlag_summe,
        "rest": pk_gesamt - abschlag_summe,
        "ohne_kalkulation": vorgang is None or not vorgang.kalkulation,
    }


@login_required
@permission_required("mbw.change_fakturierungsvorgang", raise_exception=True)
def jahresakte_spitze(request, pk, jahr):
    einsatz = _einsatz_fuer_jahresakte(pk)
    if request.method != "POST":
        return redirect("jahresakte", pk=pk, jahr=jahr)

    vorgang = Fakturierungsvorgang.objects.filter(einsatz=einsatz, jahr=jahr).first()
    daten = _spitze_vorschlag(einsatz, int(jahr), vorgang)
    if daten.get("fehlt"):
        messages.error(request, daten["fehlt"])
        return redirect("jahresakte", pk=pk, jahr=jahr)

    if vorgang is None:
        vorgang, _ = Fakturierungsvorgang.objects.get_or_create(einsatz=einsatz, jahr=jahr)
    vorgang.pk_import = daten["import_lauf"]
    vorgang.pos_bezuege = daten["bezuege"]
    vorgang.pos_umlage = daten["umlage"]
    vorgang.pos_beihilfe = daten["pos_beihilfe"]
    vorgang.spitze_rest = daten["rest"]
    vorgang.spitze_berechnet_am = now()
    vorgang.save()
    vorgang.debitor_status_aktualisieren()

    messages.success(
        request,
        f"Spitzabrechnung {jahr} übernommen: Rest {vorgang.spitze_rest} € "
        f"(PK gesamt {daten['pk_gesamt']} €, Abschläge {daten['abschlag_summe']} €).",
    )
    return redirect("jahresakte", pk=pk, jahr=jahr)


# --- Jahres-Cockpit ---------------------------------------------------------

# Pipeline-Stufen des Cockpits (Schlüssel -> Kurzlabel für die Kopfzeile)
COCKPIT_STUFEN = [
    ("kalkuliert", "Kalk."),
    ("q1", "Q1"),
    ("q2", "Q2"),
    ("q3", "Q3"),
    ("import", "SAP"),
    ("spitze", "Spitze"),
    ("rechnung", "Rechn."),
]


def _cockpit_status(forderung, bezahlt):
    if bezahlt <= 0:
        return Fakturierungsvorgang.DebitorStatus.OFFEN
    if forderung <= 0 or bezahlt >= forderung:
        return Fakturierungsvorgang.DebitorStatus.AUSGEGLICHEN
    return Fakturierungsvorgang.DebitorStatus.TEILWEISE


def _cockpit_zeilen(jahr):
    """Eine Zeile je Abrechnungs-Einsatz, der im Jahr aktiv ist, mit Pipeline-Status."""
    from datetime import date

    from django.db.models import Sum

    from .models import PersonalkostenZeile

    jahr_beginn, jahr_ende = date(jahr, 1, 1), date(jahr, 12, 31)
    einsaetze = (
        Einsatz.objects.filter(abrechnung=True, beginn__lte=jahr_ende)
        .filter(Q(ende__isnull=True) | Q(ende__gte=jahr_beginn))
        .select_related(
            "mitarbeiter", "stelle", "stelle__einrichtung", "stelle__einrichtung__traeger",
            "innenauftrag", "innenauftrag__debitor",
        )
        .order_by("mitarbeiter__nachname", "mitarbeiter__vorname")
    )

    vorgaenge = {
        v.einsatz_id: v
        for v in Fakturierungsvorgang.objects.filter(jahr=jahr).annotate(
            bezahlt=Sum("zahlungseingaenge__betrag")
        )
    }
    quartale = {}
    for eintrag in Quartalsabrechnung.objects.filter(jahr=jahr, quartal__lte=3):
        quartale.setdefault(eintrag.einsatz_id, {})[eintrag.quartal] = eintrag.betrag
    importiert = set(
        PersonalkostenZeile.objects.filter(import_lauf__jahr=jahr)
        .values_list("auftrag_nummer", "personalnummer")
        .distinct()
    )

    zeilen = []
    for einsatz in einsaetze:
        vorgang = vorgaenge.get(einsatz.pk)
        q_betraege = quartale.get(einsatz.pk, {})
        innenauftrag = getattr(einsatz, "innenauftrag", None)
        personalnummer = einsatz.mitarbeiter.personalnummer

        abschlaege = sum((b or Decimal("0") for b in q_betraege.values()), Decimal("0"))
        spitze_rest = vorgang.spitze_rest if vorgang else None
        forderung = abschlaege + (spitze_rest or Decimal("0"))
        bezahlt = (vorgang.bezahlt if vorgang and vorgang.bezahlt else Decimal("0")) if vorgang else Decimal("0")

        stufen = {
            "kalkuliert": bool(vorgang and vorgang.kalkuliert_am),
            "q1": 1 in q_betraege,
            "q2": 2 in q_betraege,
            "q3": 3 in q_betraege,
            "import": bool(innenauftrag and (innenauftrag.nummer, personalnummer) in importiert),
            "spitze": bool(vorgang and vorgang.spitze_berechnet_am),
            "rechnung": bool(vorgang and (vorgang.sap_erfasst_am or vorgang.rechnungsnummer)),
        }

        zeilen.append({
            "einsatz": einsatz,
            "vorgang": vorgang,
            "innenauftrag": innenauftrag,
            "debitor": (vorgang.debitor if vorgang and vorgang.debitor else None)
                       or (innenauftrag.debitor if innenauftrag else None),
            "stufen": stufen,
            "stufen_liste": [(label, stufen[key]) for key, label in COCKPIT_STUFEN],
            "status": _cockpit_status(forderung, bezahlt) if vorgang else None,
            "hochrechnung": vorgang.hochrechnung_gesamt if vorgang else None,
            "abschlaege": abschlaege,
            "spitze_rest": spitze_rest,
            "bezahlt": bezahlt,
            "offen": forderung - bezahlt,
        })
    return zeilen


def _cockpit_summen(zeilen):
    def summe(feld):
        return sum((z[feld] or Decimal("0") for z in zeilen), Decimal("0"))

    return {
        "faelle": len(zeilen),
        "hochrechnung": summe("hochrechnung"),
        "abschlaege": summe("abschlaege"),
        "spitze_rest": summe("spitze_rest"),
        "bezahlt": summe("bezahlt"),
        "offen": summe("offen"),
    }


@login_required
def cockpit(request):
    current_year = now().year
    try:
        jahr = int(request.GET.get("jahr", current_year))
    except (TypeError, ValueError):
        jahr = current_year

    zeilen = _cockpit_zeilen(jahr)
    context = {
        "jahr": jahr,
        "jahre": [current_year - 1, current_year, current_year + 1],
        "zeilen": zeilen,
        "summen": _cockpit_summen(zeilen),
        "stufen_kopf": [label for _, label in COCKPIT_STUFEN],
    }
    return render(request, "mbw/cockpit.html", context)


@login_required
def cockpit_export(request):
    from django.http import HttpResponse

    from . import fall_export

    current_year = now().year
    try:
        jahr = int(request.GET.get("jahr", current_year))
    except (TypeError, ValueError):
        jahr = current_year

    zeilen = _cockpit_zeilen(jahr)
    puffer = fall_export.cockpit_mappe(jahr, zeilen, _cockpit_summen(zeilen), COCKPIT_STUFEN)
    antwort = HttpResponse(
        puffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    antwort["Content-Disposition"] = f'attachment; filename="Jahres-Cockpit-{jahr}.xlsx"'
    return antwort
