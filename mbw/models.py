from django.db import models
from django.utils.timezone import localdate

from einsatz.models import Einsatz


class Innenauftrag(models.Model):
    class AndockArt(models.TextChoices):
        STELLE = "stelle", "an Stelle"
        PERSON = "person", "an Person"

    nummer = models.CharField("Innenauftrag", max_length=50, unique=True)
    bezeichnung = models.CharField(max_length=200, blank=True)

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

    besoldung_gesamt = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Aufgearbeitete Besoldungssumme des Jahres.",
    )

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

    class Meta:
        ordering = ["-jahr", "einsatz_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["einsatz", "jahr"],
                name="unique_fakturierung_pro_einsatz_und_jahr",
            )
        ]
