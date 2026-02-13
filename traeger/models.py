from django.db import models
from ansprechpartner.models import Ansprechpartner
from decimal import Decimal


class Traeger(models.Model):

    class TraegerArt(models.TextChoices):
        DIAKONISCH = "dw", "Diakonischer Träger"
        LANDESKIRCHE = "lk", "Landeskirchenamt"
        DEKANAT = "db", "Dekanat"
        KRANKENHAUS = "kr", "Krankenhäuser"
        SONSTIGE = "sn", "Sonstiger Träger" 

    name = models.CharField("Name", max_length=200, db_index=True)
    art = models.CharField("Art", max_length=2, choices=TraegerArt.choices, db_index=True)

    traeger_id = models.CharField("Träger-Id", max_length=50, blank=True, db_index=True)

    haupt_ansprechpartner = models.ForeignKey(
        Ansprechpartner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="haupt_traeger"
    )

    strasse = models.CharField("Straße", max_length=100, blank=True)
    plz = models.CharField("PLZ", max_length=5, blank=True)
    ort = models.CharField("Ort", max_length=100, blank=True)

    aktiv = models.BooleanField("Aktiv", default=True)
    bemerkung = models.TextField("Bemerkung", blank=True)

    erstellt_am = models.DateTimeField(auto_now_add=True)
    geaendert_am = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Träger"
        verbose_name_plural = "Träger"
        ordering = ["name"]

class Einrichtung(models.Model):

    class EinrichtungsArt(models.TextChoices):
        DIAKONISCH = "dw", "Diakonische Einrichtung"
        ABTEILUNG = "ab", "Abteilung"
        KIRCHENGEMEINDE = "kg", "Kirchengemeinde"
        KRANKENHAUS = "kr", "Krankenhäuser"
        SONSTIGE = "sn", "Sonstige Einrichtung"

    class Versorgungsumlage(models.TextChoices):
        KEINE = "0.00", "keine"
        VIERZIG = "0.40", "40 %"
        ACHTUNDSECHZIG = "0.68", "68 %"

    traeger = models.ForeignKey(Traeger, on_delete=models.CASCADE, related_name="einrichtungen")

    name = models.CharField(max_length=200)
    einrichtung_art = models.CharField("Einrichtungsart", max_length=100, blank=True, choices=EinrichtungsArt.choices)
    einrichtungs_id = models.CharField("Einrichtungs-Id", max_length=50, blank=True)

    strasse = models.CharField("Straße", max_length=100, blank=True)
    plz = models.CharField("PLZ", max_length=5, blank=True)
    ort = models.CharField("Ort", max_length=100, blank=True)

    ansprechpartner = models.ForeignKey(
        Ansprechpartner,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="einrichtungen"
    )
    versorgungsumlage = models.DecimalField(
        "Versorgungsumlage",
        max_digits=4,
        decimal_places=2,
        choices=[(Decimal(choice.value), choice.label)
            for choice in Versorgungsumlage
        ],
        default=Decimal(Versorgungsumlage.VIERZIG)
    )

    aktiv = models.BooleanField(default=True)
    bemerkung = models.TextField("Bemerkung", blank=True)

    erstellt_am = models.DateTimeField(auto_now_add=True)
    geaendert_am = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.traeger.name})"
    
    class Meta:
        verbose_name = "Einrichtung"
        verbose_name_plural = "Einrichtungen"
        ordering = ["name"]


class Stelle(models.Model):

    einrichtung = models.ForeignKey(Einrichtung, on_delete=models.CASCADE, related_name="stellen")

    name = models.CharField(max_length=200)
    stellen_id = models.CharField("Stellen-Id", max_length=50, blank=True)

    strasse = models.CharField("Straße", max_length=100, blank=True)
    plz = models.CharField("PLZ", max_length=5, blank=True)
    ort = models.CharField("Ort", max_length=100, blank=True)

    ansprechpartner = models.ForeignKey(
        Ansprechpartner,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="stellen"
    )
    position = models.CharField('Position', max_length=250, blank=True, help_text='Was für eine Position hat die Stelle')

    aktiv = models.BooleanField(default=True)
    bemerkung = models.TextField("Bemerkung", blank=True)

    erstellt_am = models.DateTimeField(auto_now_add=True)
    geaendert_am = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.einrichtung.traeger.name} - {self.name} - {self.position} "
    
    class Meta:
        verbose_name = "Stellen"
        verbose_name_plural = "Stellen"
        ordering = ["name"]
