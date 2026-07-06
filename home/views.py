from django.shortcuts import render
from django.utils.timezone import now

from einsatz.models import Einsatz
from mbw.models import Fakturierungsvorgang, Innenauftrag
from personal.models import Mitarbeiter


def home(request):
    if not request.user.is_authenticated:
        return render(request, "home/home.html")

    today = now().date()
    jahr = today.year
    quartal = (today.month - 1) // 3 + 1

    abrechnungsfaelle = Einsatz.objects.filter(abrechnung=True, aktiv=True)
    fakturierungen = Fakturierungsvorgang.objects.filter(jahr=jahr)

    aufgaben = [
        {
            "titel": "Abrechnungsfälle ohne Innenauftrag",
            "anzahl": abrechnungsfaelle.filter(innenauftrag__isnull=True).count(),
            "url_name": "abrechnungsliste",
            "hinweis": "Innenauftrag zuweisen, sonst kann nicht gebucht werden.",
        },
        {
            "titel": f"Q{quartal}/{jahr} noch nicht gebucht",
            "anzahl": abrechnungsfaelle.exclude(
                quartalsabrechnungen__jahr=jahr,
                quartalsabrechnungen__quartal=quartal,
            ).count(),
            "url_name": "quartalsuebersicht",
            "hinweis": "Quartalsbuchung im aktuellen Quartal fehlt.",
        },
        {
            "titel": "Fakturierungen ohne SAP-Auftragsnummer",
            "anzahl": fakturierungen.filter(sap_auftragsnummer="").count(),
            "url_name": "fakturierungsliste",
            "hinweis": "SAP-Erfassung nachtragen.",
        },
        {
            "titel": "Offene Debitoren",
            "anzahl": fakturierungen.exclude(
                debitor_status=Fakturierungsvorgang.DebitorStatus.AUSGEGLICHEN
            ).count(),
            "url_name": "fakturierungsliste",
            "hinweis": "Zahlungseingang prüfen.",
        },
    ]
    offene_aufgaben = sum(a["anzahl"] for a in aufgaben)

    context = {
        "jahr": jahr,
        "quartal": quartal,
        "aufgaben": aufgaben,
        "offene_aufgaben": offene_aufgaben,
        "aktive_mitarbeiter": Mitarbeiter.objects.filter(aktiv=True).count(),
        "aktive_einsaetze": Einsatz.objects.filter(aktiv=True).count(),
        "abrechnungsfaelle_anzahl": abrechnungsfaelle.count(),
        "freie_innenauftraege": Innenauftrag.objects.filter(
            einsatz__isnull=True, aktiv=True
        ).count(),
    }
    return render(request, "home/home.html", context)
