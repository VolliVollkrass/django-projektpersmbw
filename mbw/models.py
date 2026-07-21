from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum
from django.utils.timezone import localdate

from einsatz.models import Einsatz
from personal.models import Mitarbeiter
from traeger.models import Traeger

ORTSKLASSEN = Mitarbeiter.Ortsklasse


class Debitor(models.Model):
    """Rechnungsempfänger mit Anschrift wie im SAP-Debitorenstamm.

    Ein Träger kann mehrere Debitoren (Rechnungsanschriften) haben.
    """

    class Versandweg(models.TextChoices):
        EMAIL = "email", "E-Mail"
        POST = "post", "Post"

    sap_nummer = models.CharField(
        "SAP-Debitorennummer",
        max_length=20,
        blank=True,
        db_index=True,
        help_text="Debitorennummer im SAP S/4HANA (z. B. 1900032335)",
    )
    name = models.CharField("Name", max_length=200)
    name2 = models.CharField("Namenszusatz", max_length=200, blank=True)
    anschriftperson = models.CharField(
        "Anschriftperson",
        max_length=200,
        blank=True,
        help_text="z. B. „z. Hd. Frau Mustermann“ – erscheint im Rechnungstext",
    )
    strasse = models.CharField("Straße", max_length=150, blank=True)
    plz = models.CharField("PLZ", max_length=10, blank=True)
    ort = models.CharField("Ort", max_length=100, blank=True)
    email = models.EmailField("E-Mail", max_length=200, blank=True)
    versandweg = models.CharField(
        "Versandweg", max_length=10, choices=Versandweg.choices, blank=True
    )

    traeger = models.ForeignKey(
        Traeger,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="debitoren",
        verbose_name="Träger",
    )

    aktiv = models.BooleanField(default=True)
    bemerkung = models.TextField(blank=True)

    erstellt_am = models.DateTimeField(auto_now_add=True)
    aktualisiert_am = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.sap_nummer})" if self.sap_nummer else self.name

    class Meta:
        verbose_name = "Debitor"
        verbose_name_plural = "Debitoren"
        ordering = ["name"]


class Innenauftrag(models.Model):
    class AndockArt(models.TextChoices):
        STELLE = "stelle", "an Stelle"
        PERSON = "person", "an Person"

    KATEGORIE_LABELS = {
        "A": "personengebunden (A)",
        "F": "stellengebunden (F)",
        "U": "Sonstige (U)",
    }

    nummer = models.CharField("Innenauftrag", max_length=50, unique=True)
    bezeichnung = models.CharField(max_length=200, blank=True)
    kostenstelle = models.CharField(
        "Kostenstelle",
        max_length=30,
        blank=True,
        db_index=True,
        help_text="SAP-Kostenstelle, auf der der Auftrag bebucht wird (z. B. 3-0312P033)",
    )
    debitor = models.ForeignKey(
        Debitor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="innenauftraege",
        verbose_name="Debitor",
        help_text="Erstattungspflichtiger Rechnungsempfänger",
    )

    einsatz = models.OneToOneField(
        Einsatz,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="innenauftrag",
    )
    andock_art = models.CharField(max_length=20, choices=AndockArt.choices, blank=True)

    aktiv = models.BooleanField(default=True)
    bemerkung = models.TextField(blank=True)

    angelegt_am = models.DateTimeField(auto_now_add=True)
    aktualisiert_am = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.einsatz and not self.andock_art:
            from django.core.exceptions import ValidationError

            raise ValidationError("Bitte Andock-Art wählen, wenn ein Einsatz zugeordnet ist.")
        if not self.einsatz and self.andock_art:
            from django.core.exceptions import ValidationError

            raise ValidationError("Andock-Art nur mit zugeordnetem Einsatz setzen.")

    @property
    def ist_frei(self):
        return self.einsatz_id is None

    @property
    def kategorie(self):
        """A = personengebunden, F = stellengebunden (aus dem Nummernpräfix)."""
        praefix = self.nummer[:1].upper()
        return praefix if praefix in self.KATEGORIE_LABELS else ""

    @property
    def kategorie_label(self):
        return self.KATEGORIE_LABELS.get(self.kategorie, "")

    def __str__(self):
        return self.nummer

    class Meta:
        ordering = ["nummer"]


class Quartalsabrechnung(models.Model):
    class Art(models.TextChoices):
        ABSCHLAG = "abschlag", "Abschlagszahlung"
        SPITZE = "spitze", "Spitzabrechnung"

    QUARTAL_CHOICES = (
        (1, "Q1"),
        (2, "Q2"),
        (3, "Q3"),
        (4, "Q4"),
    )

    einsatz = models.ForeignKey(
        Einsatz,
        on_delete=models.CASCADE,
        related_name="quartalsabrechnungen",
    )
    jahr = models.PositiveSmallIntegerField()
    quartal = models.PositiveSmallIntegerField(choices=QUARTAL_CHOICES)
    art = models.CharField(max_length=20, choices=Art.choices, editable=False)
    betrag = models.DecimalField(
        "Betrag",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Abschlags- bzw. Rechnungsbetrag des Quartals",
    )
    verbucht_am = models.DateField(default=localdate)
    bemerkung = models.TextField(blank=True)

    erstellt_am = models.DateTimeField(auto_now_add=True)
    aktualisiert_am = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.art = self.Art.SPITZE if self.quartal == 4 else self.Art.ABSCHLAG
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.jahr} Q{self.quartal} - {self.einsatz_id}"

    class Meta:
        ordering = ["-jahr", "quartal", "einsatz_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["einsatz", "jahr", "quartal"],
                name="unique_quartalsabrechnung_per_einsatz_jahr_quartal",
            )
        ]


class Fakturierungsvorgang(models.Model):
    class Versandart(models.TextChoices):
        EMAIL = "email", "E-Mail"
        POST = "post", "Post"

    class DebitorStatus(models.TextChoices):
        OFFEN = "offen", "Offen"
        TEILWEISE = "teilweise", "Teilweise ausgeglichen"
        AUSGEGLICHEN = "ausgeglichen", "Ausgeglichen"

    einsatz = models.ForeignKey(
        Einsatz,
        on_delete=models.CASCADE,
        related_name="fakturierungsvorgaenge",
    )
    jahr = models.PositiveSmallIntegerField()

    debitor = models.ForeignKey(
        Debitor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="jahresakten",
        verbose_name="Debitor",
        help_text="Rechnungsempfänger; Vorbelegung kommt vom Innenauftrag",
    )

    besoldung_gesamt = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Aufgearbeitete Besoldungssumme des Jahres.",
    )

    # Kalkulation (Hochrechnung) – Snapshot der Eingaben und Monatsmatrix,
    # damit spätere Stammdatenänderungen alte Jahre nicht verfälschen
    hochrechnung_gesamt = models.DecimalField(
        "Jahres-Hochrechnung",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    abschlag_quartal = models.DecimalField(
        "Abschlag je Quartal",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Vorschlag: Hochrechnung ÷ 4, abgerundet auf volle 500 €",
    )
    kalkulation = models.JSONField(null=True, blank=True, editable=False)
    kalkuliert_am = models.DateTimeField(null=True, blank=True)

    # Spitzabrechnung – Ist-Positionen für die SAP-Rechnung
    pk_import = models.ForeignKey(
        "PersonalkostenImport",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="jahresakten",
        verbose_name="Personalkosten-Import",
        help_text="SAP-Auswertung, aus der die Ist-Positionen stammen",
    )
    pos_bezuege = models.DecimalField(
        "Position 10159 – Bezüge DiakonInnen",
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    pos_umlage = models.DecimalField(
        "Position 10167 – Umlage Versorgungsfonds",
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    pos_beihilfe = models.DecimalField(
        "Position 10171 – Beihilfepauschale/KV-Zuschuss",
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    spitze_rest = models.DecimalField(
        "Restbetrag Schlussrechnung",
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="PK gesamt abzüglich gebuchter Abschlagszahlungen",
    )
    spitze_berechnet_am = models.DateTimeField(null=True, blank=True)

    sap_auftragsnummer = models.CharField(max_length=100, blank=True)
    sap_erfasst_am = models.DateField(null=True, blank=True)

    kasse_uebergeben_am = models.DateField(null=True, blank=True)

    rechnungsnummer = models.CharField(max_length=100, blank=True)
    rechnung_pdf = models.FileField(upload_to="mbw/rechnungen/", null=True, blank=True)

    versandart = models.CharField(max_length=20, choices=Versandart.choices, blank=True)
    versandt_am = models.DateField(null=True, blank=True)

    debitor_status = models.CharField(
        max_length=20,
        choices=DebitorStatus.choices,
        default=DebitorStatus.OFFEN,
    )
    debitor_geprueft_am = models.DateField(null=True, blank=True)

    bemerkung = models.TextField(blank=True)

    erstellt_am = models.DateTimeField(auto_now_add=True)
    aktualisiert_am = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.jahr} - {self.einsatz_id}"

    # --- Debitor-Status: aus Forderung und Zahlungseingängen abgeleitet ------

    @property
    def abschlaege_summe(self):
        """Summe der gebuchten Quartals-Abschläge Q1–Q3 dieses Jahres."""
        return self.einsatz.quartalsabrechnungen.filter(
            jahr=self.jahr, quartal__lte=3
        ).aggregate(s=Sum("betrag"))["s"] or Decimal("0")

    @property
    def forderung_gesamt(self):
        """Gestellte Rechnungen = Abschläge Q1–Q3 + Spitze-Restbetrag (falls berechnet)."""
        soll = self.abschlaege_summe
        if self.spitze_rest is not None:
            soll += self.spitze_rest
        return soll

    @property
    def bezahlt_summe(self):
        return self.zahlungseingaenge.aggregate(s=Sum("betrag"))["s"] or Decimal("0")

    @property
    def offener_betrag(self):
        return self.forderung_gesamt - self.bezahlt_summe

    def status_ableiten(self):
        """Debitor-Status aus Forderung und Zahlungseingängen (ohne Speichern)."""
        soll = self.forderung_gesamt
        bezahlt = self.bezahlt_summe
        if bezahlt <= 0:
            return self.DebitorStatus.OFFEN
        if soll <= 0 or bezahlt >= soll:
            return self.DebitorStatus.AUSGEGLICHEN
        return self.DebitorStatus.TEILWEISE

    def debitor_status_aktualisieren(self):
        """Leitet den Status neu ab und speichert ihn, wenn er sich geändert hat."""
        neu = self.status_ableiten()
        if neu != self.debitor_status:
            self.debitor_status = neu
            type(self).objects.filter(pk=self.pk).update(debitor_status=neu)
        return neu

    class Meta:
        ordering = ["-jahr", "einsatz_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["einsatz", "jahr"],
                name="unique_fakturierung_pro_einsatz_und_jahr",
            )
        ]


class Zahlungseingang(models.Model):
    """Einzelne Zahlung eines Debitors auf eine Jahresakte (Fakturierungsvorgang).

    Der Debitor-Status der Jahresakte wird daraus automatisch abgeleitet
    (offen / teilweise / ausgeglichen) statt von Hand gepflegt.
    """

    vorgang = models.ForeignKey(
        Fakturierungsvorgang,
        on_delete=models.CASCADE,
        related_name="zahlungseingaenge",
        verbose_name="Jahresakte",
    )
    datum = models.DateField("Zahlungsdatum", default=localdate)
    betrag = models.DecimalField("Betrag", max_digits=12, decimal_places=2)
    bemerkung = models.CharField("Bemerkung", max_length=200, blank=True)

    erfasst_von = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    erfasst_am = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.datum:%d.%m.%Y}: {self.betrag} €"

    class Meta:
        ordering = ["datum", "id"]
        verbose_name = "Zahlungseingang"
        verbose_name_plural = "Zahlungseingänge"


BESOLDUNGSGRUPPEN = [
    (f"A{n}", f"A {n}") for n in range(3, 17)
]


class Besoldungstabelle(models.Model):
    """Grundgehaltssätze für Diakone/Diakoninnen mit Gültig-ab-Datum.

    Neue Stände entstehen i. d. R. als Vorgängertabelle × (1 + Erhöhung).
    """

    gueltig_ab = models.DateField("Gültig ab", unique=True)
    erhoehung_prozent = models.DecimalField(
        "Erhöhung %",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Erhöhung gegenüber der Vorgängertabelle in Prozent (informativ)",
    )
    bemerkung = models.TextField(blank=True)

    erstellt_am = models.DateTimeField(auto_now_add=True)

    @classmethod
    def gueltig_fuer(cls, datum):
        """Tabelle, die zum Stichtag gilt (jüngstes gueltig_ab <= datum)."""
        return cls.objects.filter(gueltig_ab__lte=datum).order_by("-gueltig_ab").first()

    def __str__(self):
        return f"Besoldung ab {self.gueltig_ab:%d.%m.%Y}"

    class Meta:
        verbose_name = "Besoldungstabelle"
        verbose_name_plural = "Besoldungstabellen"
        ordering = ["-gueltig_ab"]


class Besoldungsbetrag(models.Model):
    tabelle = models.ForeignKey(
        Besoldungstabelle, on_delete=models.CASCADE, related_name="betraege"
    )
    gruppe = models.CharField("Besoldungsgruppe", max_length=5, choices=BESOLDUNGSGRUPPEN)
    stufe = models.PositiveSmallIntegerField("Stufe")
    betrag = models.DecimalField("Monatsbetrag", max_digits=9, decimal_places=2)

    def __str__(self):
        return f"{self.gruppe} Stufe {self.stufe}: {self.betrag} €"

    class Meta:
        verbose_name = "Besoldungsbetrag"
        verbose_name_plural = "Besoldungsbeträge"
        ordering = ["gruppe", "stufe"]
        constraints = [
            models.UniqueConstraint(
                fields=["tabelle", "gruppe", "stufe"],
                name="unique_besoldungsbetrag_pro_tabelle_gruppe_stufe",
            )
        ]


class Familienzuschlagtabelle(models.Model):
    """Orts- und Familienzuschlag (OFZ) mit Gültig-ab-Datum."""

    gueltig_ab = models.DateField("Gültig ab", unique=True)
    erhoehung_prozent = models.DecimalField(
        "Erhöhung %", max_digits=5, decimal_places=2, null=True, blank=True
    )
    bemerkung = models.TextField(blank=True)

    erstellt_am = models.DateTimeField(auto_now_add=True)

    @classmethod
    def gueltig_fuer(cls, datum):
        return cls.objects.filter(gueltig_ab__lte=datum).order_by("-gueltig_ab").first()

    def __str__(self):
        return f"OFZ ab {self.gueltig_ab:%d.%m.%Y}"

    class Meta:
        verbose_name = "Familienzuschlagtabelle"
        verbose_name_plural = "Familienzuschlagtabellen"
        ordering = ["-gueltig_ab"]


class Familienzuschlagzeile(models.Model):
    """OFZ-Monatsbeträge je Ortsklasse (Stufe L/V, Stufe 1/2, Kinderzuschläge)."""

    tabelle = models.ForeignKey(
        Familienzuschlagtabelle, on_delete=models.CASCADE, related_name="zeilen"
    )
    ortsklasse = models.CharField(max_length=3, choices=ORTSKLASSEN.choices)
    stufe_l = models.DecimalField("Stufe L", max_digits=8, decimal_places=2, null=True, blank=True)
    stufe_v = models.DecimalField("Stufe V", max_digits=8, decimal_places=2, null=True, blank=True)
    stufe_1 = models.DecimalField("Stufe 1", max_digits=8, decimal_places=2, null=True, blank=True)
    stufe_2 = models.DecimalField("Stufe 2", max_digits=8, decimal_places=2, null=True, blank=True)
    kind_3 = models.DecimalField(
        "zzgl. 3. Kind", max_digits=8, decimal_places=2, null=True, blank=True
    )
    kind_weitere = models.DecimalField(
        "zzgl. je weiterem Kind", max_digits=8, decimal_places=2, null=True, blank=True
    )

    def __str__(self):
        return f"{self.tabelle} – Ortsklasse {self.ortsklasse}"

    class Meta:
        verbose_name = "Familienzuschlag-Zeile"
        verbose_name_plural = "Familienzuschlag-Zeilen"
        ordering = ["ortsklasse"]
        constraints = [
            models.UniqueConstraint(
                fields=["tabelle", "ortsklasse"],
                name="unique_fz_zeile_pro_tabelle_ortsklasse",
            )
        ]


class FZKinderErhoehung(models.Model):
    """Erhöhungsbeträge je Kind für A 8 bis A 10 (je Ortsklasse)."""

    tabelle = models.ForeignKey(
        Familienzuschlagtabelle, on_delete=models.CASCADE, related_name="kinder_erhoehungen"
    )
    ortsklasse = models.CharField(max_length=3, choices=ORTSKLASSEN.choices)
    gruppe = models.CharField("Besoldungsgruppe", max_length=5, choices=BESOLDUNGSGRUPPEN)
    betrag = models.DecimalField("Erhöhung je Kind", max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.tabelle} – {self.gruppe} Ortsklasse {self.ortsklasse}: {self.betrag} €"

    class Meta:
        verbose_name = "FZ-Kindererhöhung (A8–A10)"
        verbose_name_plural = "FZ-Kindererhöhungen (A8–A10)"
        ordering = ["gruppe", "ortsklasse"]
        constraints = [
            models.UniqueConstraint(
                fields=["tabelle", "ortsklasse", "gruppe"],
                name="unique_fz_kindererhoehung",
            )
        ]


class Zulagensatz(models.Model):
    """Monatsbeträge für Zulagen (Struktur-, Amts-, Heimzulage) mit Gültig-ab."""

    class Art(models.TextChoices):
        STRUKTUR = "struktur", "Strukturzulage (A 9 – A 13)"
        AMT = "amt", "Amtszulage"
        HEIM = "heim", "Heimzulage"
        HEIMLEITER = "heimleiter", "Heimleiterzulage"

    art = models.CharField(max_length=20, choices=Art.choices)
    variante = models.CharField(
        max_length=20,
        blank=True,
        help_text="z. B. „A9 I“ bei Amtszulagen; leer bei Struktur-/Heimzulage",
    )
    gueltig_ab = models.DateField("Gültig ab")
    betrag = models.DecimalField("Monatsbetrag", max_digits=8, decimal_places=2)
    bemerkung = models.TextField(blank=True)

    @classmethod
    def gueltig_fuer(cls, art, datum, variante=""):
        return (
            cls.objects.filter(art=art, variante=variante, gueltig_ab__lte=datum)
            .order_by("-gueltig_ab")
            .first()
        )

    def __str__(self):
        zusatz = f" {self.variante}" if self.variante else ""
        return f"{self.get_art_display()}{zusatz} ab {self.gueltig_ab:%d.%m.%Y}: {self.betrag} €"

    class Meta:
        verbose_name = "Zulagensatz"
        verbose_name_plural = "Zulagensätze"
        ordering = ["art", "variante", "-gueltig_ab"]
        constraints = [
            models.UniqueConstraint(
                fields=["art", "variante", "gueltig_ab"],
                name="unique_zulagensatz",
            )
        ]


class Beihilfesatz(models.Model):
    """Monatsbeiträge der Beihilfeablöseversicherung (Bayer. Beamtenkrankenkasse).

    Tarif 814 = Pauschalbeitrag, Tarif 830 = altersabhängige Pauschale.
    Quelle: jährliche Beitragstabelle der BBK („Beihilfeversicherungspauschale“).
    """

    class Tarif(models.TextChoices):
        T814 = "814", "Tarif 814 (Pauschalbeitrag)"
        T830 = "830", "Tarif 830 (altersabhängig)"

    class Kategorie(models.TextChoices):
        ERWACHSEN = "erwachsen", "Erwachsene"
        KIND = "kind", "Kinder"

    jahr = models.PositiveSmallIntegerField("Jahr")
    tarif = models.CharField(max_length=5, choices=Tarif.choices)
    kategorie = models.CharField(max_length=10, choices=Kategorie.choices)
    alter_bis = models.PositiveSmallIntegerField(
        "Alter bis",
        null=True,
        blank=True,
        help_text="Obergrenze der Altersgruppe einschließlich; leer = keine Obergrenze",
    )
    satz = models.DecimalField("Monatsbeitrag", max_digits=8, decimal_places=2)

    @classmethod
    def satz_fuer(cls, jahr, tarif, alter):
        """Erwachsenen-Monatsbeitrag für ein Lebensalter (kleinste passende Altersgruppe)."""
        saetze = cls.objects.filter(jahr=jahr, tarif=tarif, kategorie=cls.Kategorie.ERWACHSEN)
        passend = (
            saetze.filter(alter_bis__gte=alter).order_by("alter_bis").first()
            or saetze.filter(alter_bis__isnull=True).first()
        )
        return passend.satz if passend else None

    @classmethod
    def kindersatz_fuer(cls, jahr, tarif):
        satz = cls.objects.filter(jahr=jahr, tarif=tarif, kategorie=cls.Kategorie.KIND).first()
        return satz.satz if satz else None

    def __str__(self):
        gruppe = f"bis {self.alter_bis} J." if self.alter_bis else "ohne Obergrenze"
        if self.kategorie == self.Kategorie.KIND:
            gruppe = "Kinder"
        return f"{self.jahr} Tarif {self.tarif} {gruppe}: {self.satz} €"

    class Meta:
        verbose_name = "Beihilfesatz"
        verbose_name_plural = "Beihilfesätze"
        ordering = ["-jahr", "tarif", "kategorie", "alter_bis"]
        constraints = [
            models.UniqueConstraint(
                fields=["jahr", "tarif", "kategorie", "alter_bis"],
                name="unique_beihilfesatz",
            )
        ]


class Mietenstufe(models.Model):
    """Ortsklassen-Verzeichnis: Mietenstufe nach Wohngeldverordnung.

    Gemeinden über 10.000 Einwohner sind direkt zugeordnet, kleinere über
    ihren Landkreis (BayBesG Art. 36).
    """

    class Art(models.TextChoices):
        GEMEINDE = "gemeinde", "Gemeinde"
        KREIS = "kreis", "Landkreis"

    art = models.CharField(max_length=10, choices=Art.choices)
    name = models.CharField("Name", max_length=200, db_index=True)
    stufe = models.CharField("Mietenstufe", max_length=3, choices=ORTSKLASSEN.choices)

    def __str__(self):
        return f"{self.name} ({self.get_art_display()}): {self.stufe}"

    class Meta:
        verbose_name = "Mietenstufe"
        verbose_name_plural = "Mietenstufen"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["art", "name"], name="unique_mietenstufe")
        ]


class PersonalkostenImport(models.Model):
    """Ein eingelesener SAP-Abrechnungslauf („Dynamische Listenausgabe“)."""

    dateiname = models.CharField(max_length=255)
    jahr = models.PositiveSmallIntegerField(
        "Abrechnungsjahr",
        help_text="Aus den Für-Perioden der Datei abgeleitet",
    )
    bemerkung = models.TextField(blank=True)

    hochgeladen_am = models.DateTimeField(auto_now_add=True)
    hochgeladen_von = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="pk_importe",
    )

    def __str__(self):
        return f"{self.dateiname} ({self.jahr})"

    class Meta:
        verbose_name = "Personalkosten-Import"
        verbose_name_plural = "Personalkosten-Importe"
        ordering = ["-hochgeladen_am"]


class PersonalkostenZeile(models.Model):
    """Eine Buchungszeile aus der SAP-Auswertung."""

    import_lauf = models.ForeignKey(
        PersonalkostenImport, on_delete=models.CASCADE, related_name="zeilen"
    )
    lfd_nr = models.PositiveIntegerField("lfd. Nr.")

    personalnummer = models.CharField(max_length=10, db_index=True)
    nachname = models.CharField(max_length=100)
    vorname = models.CharField(max_length=100)
    lbe = models.CharField("L B E", max_length=20, blank=True)
    kostenstelle = models.CharField(max_length=30, blank=True)
    auftrag_nummer = models.CharField("Auftrag", max_length=50, db_index=True)
    hauptbuchkonto = models.CharField("Hauptb", max_length=10, db_index=True)
    lohnart = models.CharField("LArt", max_length=10)
    lohnart_text = models.CharField("Lohnart-Langtext", max_length=100, blank=True)
    betrag = models.DecimalField(max_digits=12, decimal_places=2)
    waehrung = models.CharField(max_length=5, default="EUR")
    text = models.CharField(max_length=50, blank=True)
    fuer_periode = models.CharField("Fürper.", max_length=6, blank=True)
    in_periode = models.CharField("Inper.", max_length=6, blank=True)

    # Storno-Paar: +X und −X gleicher Lohnart/Für-Periode heben sich auf
    storno_partner = models.OneToOneField(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="storno_gegenstueck",
    )

    innenauftrag = models.ForeignKey(
        Innenauftrag, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="personalkosten_zeilen",
    )
    mitarbeiter = models.ForeignKey(
        Mitarbeiter, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="personalkosten_zeilen",
    )

    @property
    def ist_storniert(self):
        return self.storno_partner_id is not None

    def __str__(self):
        return f"{self.lfd_nr}: {self.personalnummer} {self.lohnart} {self.betrag}"

    class Meta:
        verbose_name = "Personalkosten-Zeile"
        verbose_name_plural = "Personalkosten-Zeilen"
        ordering = ["lfd_nr"]
        constraints = [
            models.UniqueConstraint(
                fields=["import_lauf", "lfd_nr"], name="unique_pk_zeile_lfd_nr"
            )
        ]
