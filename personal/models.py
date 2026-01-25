from django.db import models
from django.contrib.auth.models import User
from datetime import date


class Mitarbeiter(models.Model):

    class Anstellung(models.TextChoices):
        OER = "oer", "öffentlich-rechtlich"
        PR = "pr", "privatrechtlich"

    class Familienstand(models.TextChoices):
        LEDIG = "ledig", "Ledig"
        VERHEIRATET = "verheiratet", "Verheiratet"
        GESCHIEDEN = "geschieden", "Geschieden"
        VERWITWET = "verwitwet", "Verwitwet"
        PARTNERSCHAFT = "partnerschaft", "Eingetragene Partnerschaft"

    class Besoldung(models.TextChoices):
        A8 = "A8", "A8"
        A9 = "A9", "A9"
        A10 = "A10", "A10"
        A11 = "A11", "A11"
        A12 = "A12", "A12"
        A13 = "A13", "A13"
        A14 = "A14", "A14"
        A15 = "A15", "A15"

    class Geschlecht(models.TextChoices):
        W = "w", "weiblich"
        M = "m", "männlich"
        D = "d", "divers"

    class Dienststand(models.TextChoices):
        DIAKON = "diakon", "Diakon"
        PFARRER = "pfarrer", "Pfarrer"
        RELPAD = "relpad", "Religionspädagoge"
        SOZPAD = "sozpad", "Sozialpädagoge"
        KIMU = "kimu", "Kirchenmusiker"
    
    # 🔹 Grunddaten
    personalnummer = models.CharField("Personalnummer", max_length=10,primary_key=True, db_index=True)
    geschlecht = models.CharField("Geschlecht", max_length=1,choices=Geschlecht.choices, default=Geschlecht.M)
    vorname = models.CharField("Vorname", max_length=100, db_index=True)
    nachname = models.CharField("Nachname", max_length=100, db_index=True)
    geburtsdatum = models.DateField("Geburtsdatum")

    # 🔹 Kontaktdaten
    email = models.EmailField('E-Mail', max_length=100, null=True, blank=True)
    telefon_privat = models.CharField('Telefon Privat', max_length=30, blank=True)
    telefon_dienst = models.CharField('Telefon Dienstlich', max_length=30, blank=True)
    strasse = models.CharField('Straße', max_length=150, blank=True)
    plz = models.CharField('PLZ',max_length=5, blank=True)    
    ort = models.CharField('Ort', max_length=100, blank=True)


    # 🔹 Dienstrechtlicher Status
    anstellungs_status = models.CharField('Dienststand',max_length=100, choices=Anstellung.choices, default=Anstellung.OER)
    dienststand = models.CharField('Dienststand',max_length=100, choices=Dienststand.choices, default=Dienststand.DIAKON)
    status_besoldung = models.CharField("Besoldungsgruppe", max_length=10, choices=Besoldung.choices, default=Besoldung.A10)  # A10, E9 etc.
    status_stufe = models.PositiveSmallIntegerField("Besoldungsstufe", default=4)

    # 🔹 Familie (für Zuschläge) sind in einem extra Model
    familienstand = models.CharField(
        max_length=30,
        choices=Familienstand.choices,
        default=Familienstand.LEDIG
    )
    kinder = models.PositiveSmallIntegerField(default=0)
    kindergeldberechtigt = models.BooleanField(default=False)
    anspruch_voll = models.BooleanField('Voller OFZ-Anspruch',default=False)   

    # 🔹 Verwaltung
    aktiv = models.BooleanField(default=True)
    bemerkung = models.TextField(blank=True)
    angelegt_von = models.ForeignKey(User, related_name="angelegte_mitarbeiter", on_delete=models.SET_NULL, null=True, blank=True)
    angelegt_am = models.DateTimeField(auto_now_add=True)
    aktualisiert_am = models.DateTimeField(auto_now=True)

    @property
    def alter(self):
        heute = date.today()
        return heute.year - self.geburtsdatum.year - (
            (heute.month, heute.day) < (self.geburtsdatum.month, self.geburtsdatum.day)
        )

    def get_diakon_titel(self):
        if self.geschlecht == 'w':
            return "Diakonin"
        elif self.geschlecht == 'm':
            return "Diakon"
        else:
            return "Diakon*in"

    def __str__(self):
        return f"{self.nachname}, {self.vorname} - {self.personalnummer}"
    
    class Meta:
        ordering = ["nachname", "vorname"]
        verbose_name = "Mitarbeiter"
        verbose_name_plural = "Mitarbeiter"