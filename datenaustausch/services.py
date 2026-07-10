"""Import-Durchführung: erst Vorschau (kompletter Probelauf, wird zurückgerollt),
dann echter Import – beides über denselben Code, damit die Vorschau exakt dem
späteren Import entspricht.

Alle Blätter laufen in EINER Transaktion in fester Reihenfolge, damit z. B.
Einrichtungen die im selben Durchlauf angelegten Träger finden. Sobald
irgendwo ein Fehler auftritt, wird nichts geschrieben (alles oder nichts).
"""

from dataclasses import dataclass, field

from django.db import transaction

from .xlsx import mappe_lesen


@dataclass
class BlattErgebnis:
    sheet_name: str
    zeilen: int = 0
    neu: int = 0
    aktualisiert: int = 0
    unveraendert: int = 0
    fehler: list = field(default_factory=list)  # Liste von (excel_zeile, meldung)

    @property
    def hat_fehler(self):
        return bool(self.fehler)


class _VorschauRollback(Exception):
    """Internes Signal: Probelauf beendet, Änderungen verwerfen."""


def _fehltext(err):
    text = str(err)
    return text if text else err.__class__.__name__


def _blatt_importieren(config, daten, kopf_zeile, user):
    resource = config.resource_class()
    result = resource.import_data(
        daten,
        dry_run=False,           # Schreiben lassen – die umgebende Transaktion
        use_transactions=False,  # entscheidet über Commit oder Rollback
        rollback_on_validation_errors=False,
        user=user,
    )

    ergebnis = BlattErgebnis(sheet_name=config.sheet_name, zeilen=len(daten))
    totals = result.totals
    ergebnis.neu = totals.get("new", 0)
    ergebnis.aktualisiert = totals.get("update", 0)
    ergebnis.unveraendert = totals.get("skip", 0)

    for fehler in result.base_errors:
        ergebnis.fehler.append(("–", _fehltext(fehler.error)))

    for nummer, zeilen_fehler in result.row_errors():
        excel_zeile = kopf_zeile + nummer
        for fehler in zeilen_fehler:
            ergebnis.fehler.append((excel_zeile, _fehltext(fehler.error)))

    for ungueltig in result.invalid_rows:
        excel_zeile = kopf_zeile + ungueltig.number
        err = ungueltig.error
        if hasattr(err, "error_dict"):
            for feld, meldungen in err.message_dict.items():
                prefix = "" if feld == "__all__" else f"{feld}: "
                for meldung in meldungen:
                    ergebnis.fehler.append((excel_zeile, f"{prefix}{meldung}"))
        else:
            for meldung in getattr(err, "messages", [str(err)]):
                ergebnis.fehler.append((excel_zeile, meldung))

    return ergebnis


def import_ausfuehren(datei, user, commit):
    """Führt den Import aller bekannten Blätter aus.

    commit=False: Probelauf – alles wird zurückgerollt (Vorschau).
    commit=True: echter Import – wird nur gespeichert, wenn KEIN Blatt Fehler hat.

    Rückgabe: (ergebnisse, gespeichert)
    """
    blaetter = mappe_lesen(datei)
    ergebnisse = []
    gespeichert = False

    if not blaetter:
        return ergebnisse, gespeichert

    try:
        with transaction.atomic():
            for config, daten, kopf_zeile in blaetter:
                ergebnisse.append(_blatt_importieren(config, daten, kopf_zeile, user))

            hat_fehler = any(e.hat_fehler for e in ergebnisse)
            if not commit or hat_fehler:
                raise _VorschauRollback()
            gespeichert = True
    except _VorschauRollback:
        pass

    return ergebnisse, gespeichert
