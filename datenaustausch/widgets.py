"""Gemeinsame import_export-Widgets für das Vorlagenformat.

Die Excel-Vorlage arbeitet mit deutschen Klartext-Werten ("Ja", "Diakonischer
Träger", "40 %") und fachlichen Schlüsseln (Träger-Id, Einrichtungs-Id,
Stellen-Id, Personalnummer, E-Mail). Diese Widgets übersetzen beim Import in
DB-Werte und beim Export zurück in den Klartext, sodass eine exportierte
Datei unverändert wieder importiert werden kann.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from import_export import widgets


def _text(value):
    """Zellwert in einen getrimmten String wandeln (Excel liefert auch Zahlen)."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


class JaNeinWidget(widgets.Widget):
    """Boolesche Spalte als 'Ja'/'Nein' (tolerant gegen true/1/x usw.)."""

    WAHR = {"ja", "j", "true", "wahr", "1", "x"}
    FALSCH = {"nein", "n", "false", "falsch", "0"}

    def __init__(self, default=None):
        self.default = default

    def clean(self, value, row=None, **kwargs):
        if value is None or value == "":
            return self.default
        if isinstance(value, bool):
            return value
        s = _text(value).lower()
        if s in self.WAHR:
            return True
        if s in self.FALSCH:
            return False
        raise ValueError(f"'{value}' ist kein gültiger Ja/Nein-Wert.")

    def render(self, value, obj=None, **kwargs):
        if value is None:
            return ""
        return "Ja" if value else "Nein"


class ChoiceLabelWidget(widgets.Widget):
    """Choices-Feld: akzeptiert Label ("Diakonischer Träger") oder Code ("dw"),
    exportiert immer das Label."""

    def __init__(self, choices, default=None):
        self.choices = [(str(code), str(label)) for code, label in choices]
        self.default = default

    def clean(self, value, row=None, **kwargs):
        s = _text(value)
        if not s:
            if self.default is not None:
                return self.default
            return ""
        for code, label in self.choices:
            if s.lower() in (label.lower(), code.lower()):
                return code
        gueltig = ", ".join(label for _, label in self.choices)
        raise ValueError(f"'{value}' ist ungültig. Erlaubte Werte: {gueltig}.")

    def render(self, value, obj=None, **kwargs):
        s = "" if value is None else str(value)
        for code, label in self.choices:
            if s == code:
                return label
        return s


class DeutschesDatumWidget(widgets.Widget):
    """Datum als JJJJ-MM-TT oder TT.MM.JJJJ; Excel-Datumszellen direkt."""

    FORMATE = ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y")

    def clean(self, value, row=None, **kwargs):
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        s = _text(value)
        for fmt in self.FORMATE:
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        raise ValueError(
            f"'{value}' ist kein gültiges Datum (erwartet JJJJ-MM-TT oder TT.MM.JJJJ)."
        )

    def render(self, value, obj=None, **kwargs):
        return value.strftime("%Y-%m-%d") if value else ""


class ProzentAnteilWidget(widgets.Widget):
    """Dezimaler Anteil (0.00–1.00), tolerant: '0.5', '0,5', '50 %', '50%'.

    Export als Dezimalwert mit Punkt (z. B. '0.50'), wie in der Vorlage.
    """

    def __init__(self, default=None):
        self.default = default

    def clean(self, value, row=None, **kwargs):
        if value is None or value == "":
            return self.default
        s = _text(value).replace(",", ".").replace(" ", "")
        prozent = s.endswith("%")
        if prozent:
            s = s.rstrip("%")
        try:
            zahl = Decimal(s)
        except InvalidOperation:
            raise ValueError(f"'{value}' ist keine gültige Zahl.")
        if prozent or zahl > 1:
            zahl = zahl / Decimal("100")
        return zahl.quantize(Decimal("0.01"))

    def render(self, value, obj=None, **kwargs):
        if value is None:
            return ""
        return f"{Decimal(value):.2f}"


class VersorgungsumlageWidget(widgets.Widget):
    """Versorgungsumlage: 'keine' / '40 %' / '68 %' (auch 0.4, '0,68' …)."""

    STUFEN = [
        (Decimal("0.00"), "keine"),
        (Decimal("0.40"), "40 %"),
        (Decimal("0.68"), "68 %"),
    ]

    def clean(self, value, row=None, **kwargs):
        s = _text(value)
        if not s:
            return Decimal("0.40")  # Modell-Default
        for wert, label in self.STUFEN:
            if s.lower() == label.lower():
                return wert
        zahl = ProzentAnteilWidget().clean(s)
        for wert, _label in self.STUFEN:
            if zahl == wert:
                return wert
        gueltig = ", ".join(label for _, label in self.STUFEN)
        raise ValueError(f"'{value}' ist ungültig. Erlaubte Werte: {gueltig}.")

    def render(self, value, obj=None, **kwargs):
        if value is None:
            return ""
        for wert, label in self.STUFEN:
            if Decimal(value) == wert:
                return label
        return str(value)


class GanzzahlWidget(widgets.Widget):
    """Ganzzahl mit Default für leere Zellen (z. B. Kinder = 0, Stufe = 4)."""

    def __init__(self, default=None):
        self.default = default

    def clean(self, value, row=None, **kwargs):
        if value is None or value == "":
            return self.default
        try:
            return int(_text(value))
        except ValueError:
            raise ValueError(f"'{value}' ist keine gültige ganze Zahl.")

    def render(self, value, obj=None, **kwargs):
        return "" if value is None else str(value)


class TextWidget(widgets.Widget):
    """Text-Zelle; wandelt Zahlen (PLZ, Personalnummer) sauber in Strings."""

    def clean(self, value, row=None, **kwargs):
        return _text(value)

    def render(self, value, obj=None, **kwargs):
        return "" if value is None else str(value)


class AnsprechpartnerEmailWidget(widgets.ForeignKeyWidget):
    """Ansprechpartner-Verweis über die E-Mail-Adresse (optional)."""

    def __init__(self, model):
        super().__init__(model, field="email")

    def clean(self, value, row=None, **kwargs):
        email = _text(value)
        if not email:
            return None
        qs = self.model.objects.filter(email__iexact=email)
        anzahl = qs.count()
        if anzahl == 1:
            return qs.first()
        if anzahl == 0:
            raise ValueError(
                f"Kein Ansprechpartner mit E-Mail '{email}' gefunden – "
                "bitte zuerst im Blatt 'Ansprechpartner' anlegen."
            )
        raise ValueError(f"Mehrere Ansprechpartner mit E-Mail '{email}' vorhanden.")

    def render(self, value, obj=None, **kwargs):
        return value.email if value else ""


class TraegerIdWidget(widgets.ForeignKeyWidget):
    """Träger-Verweis über die (eindeutige) Träger-Id."""

    def __init__(self, model):
        super().__init__(model, field="traeger_id")

    def clean(self, value, row=None, **kwargs):
        tid = _text(value)
        if not tid:
            raise ValueError("Träger-Id fehlt.")
        try:
            return self.model.objects.get(traeger_id=tid)
        except self.model.DoesNotExist:
            raise ValueError(
                f"Kein Träger mit Träger-Id '{tid}' gefunden – "
                "bitte zuerst im Blatt 'Träger' anlegen."
            )
        except self.model.MultipleObjectsReturned:
            raise ValueError(f"Träger-Id '{tid}' ist mehrfach vergeben – bitte in der App bereinigen.")

    def render(self, value, obj=None, **kwargs):
        return value.traeger_id if value else ""


class SammelIdWidget(widgets.Widget):
    """Verweis über eine fachliche Id, die als Sammel-Id mehrfach vorkommen darf
    (Einrichtungs-Id, Stellen-Id). Bei Mehrdeutigkeit entscheidet die
    zugehörige Namens-Spalte im selben Blatt."""

    def __init__(self, model, id_feld, id_spalte, name_spalte, blatt_hinweis):
        self.model = model
        self.id_feld = id_feld
        self.id_spalte = id_spalte
        self.name_spalte = name_spalte
        self.blatt_hinweis = blatt_hinweis

    def clean(self, value, row=None, **kwargs):
        kennung = _text(value)
        if not kennung:
            raise ValueError(f"{self.id_spalte} fehlt.")
        qs = self.model.objects.filter(**{self.id_feld: kennung})
        name = _text((row or {}).get(self.name_spalte))
        if name:
            qs = qs.filter(name__iexact=name)
        treffer = list(qs[:6])
        if len(treffer) == 1:
            return treffer[0]
        if not treffer:
            zusatz = f" und Name '{name}'" if name else ""
            raise ValueError(
                f"Kein Eintrag mit {self.id_spalte} '{kennung}'{zusatz} gefunden – "
                f"bitte zuerst im Blatt '{self.blatt_hinweis}' anlegen."
            )
        namen = ", ".join(f"'{t.name}'" for t in treffer[:5])
        raise ValueError(
            f"{self.id_spalte} '{kennung}' ist eine Sammel-Id mit mehreren Einträgen "
            f"({namen}) – bitte die Spalte '{self.name_spalte}' ausfüllen."
        )

    def render(self, value, obj=None, **kwargs):
        return getattr(value, self.id_feld) if value else ""
