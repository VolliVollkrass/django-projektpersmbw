import uuid
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .registry import SCHREIB_RECHTE, SHEETS, SHEETS_BY_SLUG
from .services import import_ausfuehren
from .xlsx import mappe_schreiben

VORLAGE_PFAD = Path(settings.BASE_DIR) / "import_vorlagen" / "Stammdaten-Import-Vorlage.xlsx"
UPLOAD_VERZEICHNIS = Path(settings.MEDIA_ROOT) / "import_tmp"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
SESSION_KEY = "datenimport"

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _upload_pfad(token):
    # Token stammt aus uuid4().hex – kein Pfadanteil möglich
    return UPLOAD_VERZEICHNIS / f"{token}.xlsx"


def _upload_aufraeumen(request):
    info = request.session.pop(SESSION_KEY, None)
    if info:
        _upload_pfad(info["token"]).unlink(missing_ok=True)


@login_required
@permission_required(SCHREIB_RECHTE, raise_exception=True)
def uebersicht(request):
    _upload_aufraeumen(request)
    return render(request, "datenaustausch/uebersicht.html", {"sheets": SHEETS})


@login_required
@permission_required(SCHREIB_RECHTE, raise_exception=True)
def vorlage_download(request):
    if not VORLAGE_PFAD.exists():
        raise Http404("Vorlage nicht gefunden.")
    response = HttpResponse(VORLAGE_PFAD.read_bytes(), content_type=XLSX_MIME)
    response["Content-Disposition"] = 'attachment; filename="Stammdaten-Import-Vorlage.xlsx"'
    return response


@login_required
@permission_required(SCHREIB_RECHTE, raise_exception=True)
def export_alle(request):
    datensaetze = []
    for config in SHEETS:
        resource = config.resource_class()
        datensaetze.append((config, resource.export()))

    puffer = mappe_schreiben(datensaetze)
    datum = timezone.localdate().isoformat()
    response = HttpResponse(puffer.read(), content_type=XLSX_MIME)
    response["Content-Disposition"] = f'attachment; filename="diakon-Stammdaten-{datum}.xlsx"'
    return response


@login_required
@permission_required(SCHREIB_RECHTE, raise_exception=True)
def export_einzeln(request, slug):
    config = SHEETS_BY_SLUG.get(slug)
    if config is None:
        raise Http404

    queryset = config.model.objects.all()
    query = request.GET.get("q", "").strip()
    if query and config.such_filter:
        queryset = queryset.filter(config.such_filter(query))

    resource = config.resource_class()
    puffer = mappe_schreiben([(config, resource.export(queryset=queryset))])
    datum = timezone.localdate().isoformat()
    response = HttpResponse(puffer.read(), content_type=XLSX_MIME)
    response["Content-Disposition"] = f'attachment; filename="diakon-{slug}-{datum}.xlsx"'
    return response


@login_required
@permission_required(SCHREIB_RECHTE, raise_exception=True)
@require_POST
def import_vorschau(request):
    _upload_aufraeumen(request)

    datei = request.FILES.get("datei")
    if datei is None:
        messages.error(request, "Bitte eine Excel-Datei (.xlsx) auswählen.")
        return redirect("datenaustausch")
    if not datei.name.lower().endswith(".xlsx"):
        messages.error(request, "Nur .xlsx-Dateien werden unterstützt.")
        return redirect("datenaustausch")
    if datei.size > MAX_UPLOAD_BYTES:
        messages.error(request, "Die Datei ist größer als 10 MB.")
        return redirect("datenaustausch")

    UPLOAD_VERZEICHNIS.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    pfad = _upload_pfad(token)
    with open(pfad, "wb") as ziel:
        for chunk in datei.chunks():
            ziel.write(chunk)

    try:
        ergebnisse, _ = import_ausfuehren(pfad, request.user, commit=False)
    except Exception as exc:
        pfad.unlink(missing_ok=True)
        messages.error(request, f"Die Datei konnte nicht gelesen werden: {exc}")
        return redirect("datenaustausch")

    if not ergebnisse:
        pfad.unlink(missing_ok=True)
        messages.error(
            request,
            "In der Datei wurde kein bekanntes Blatt mit Daten gefunden. "
            "Erwartet werden Blätter wie in der Vorlage (Ansprechpartner, Träger, …).",
        )
        return redirect("datenaustausch")

    request.session[SESSION_KEY] = {"token": token, "dateiname": datei.name}
    hat_fehler = any(e.hat_fehler for e in ergebnisse)
    return render(
        request,
        "datenaustausch/vorschau.html",
        {
            "ergebnisse": ergebnisse,
            "hat_fehler": hat_fehler,
            "dateiname": datei.name,
        },
    )


@login_required
@permission_required(SCHREIB_RECHTE, raise_exception=True)
@require_POST
def import_bestaetigen(request):
    info = request.session.get(SESSION_KEY)
    if not info or not _upload_pfad(info["token"]).exists():
        messages.error(request, "Keine Import-Datei mehr vorhanden – bitte erneut hochladen.")
        return redirect("datenaustausch")

    pfad = _upload_pfad(info["token"])
    try:
        ergebnisse, gespeichert = import_ausfuehren(pfad, request.user, commit=True)
    finally:
        _upload_aufraeumen(request)

    if not gespeichert:
        messages.error(
            request,
            "Der Import wurde NICHT gespeichert, weil Fehler aufgetreten sind "
            "(die Daten haben sich seit der Vorschau evtl. geändert). Bitte erneut hochladen.",
        )
        return redirect("datenaustausch")

    neu = sum(e.neu for e in ergebnisse)
    aktualisiert = sum(e.aktualisiert for e in ergebnisse)
    unveraendert = sum(e.unveraendert for e in ergebnisse)
    messages.success(
        request,
        f"Import erfolgreich: {neu} neu angelegt, {aktualisiert} aktualisiert, "
        f"{unveraendert} unverändert übersprungen.",
    )
    return redirect("datenaustausch")


@login_required
@permission_required(SCHREIB_RECHTE, raise_exception=True)
@require_POST
def import_abbrechen(request):
    _upload_aufraeumen(request)
    messages.info(request, "Import abgebrochen – es wurde nichts gespeichert.")
    return redirect("datenaustausch")
