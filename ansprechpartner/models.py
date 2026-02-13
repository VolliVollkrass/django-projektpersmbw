from django.db import models

GESCHLECHT = [
    ('w', 'weiblich'),
    ('m', 'männlich'),
    ('d', 'divers'),
    ]

class Ansprechpartner(models.Model):
    GESCHLECHT = [
        ('w', 'weiblich'),
        ('m', 'männlich'),
        ('d', 'divers'),
        ]
    
    geschlecht = models.CharField("Geschlecht", max_length=1,choices=GESCHLECHT, default="m")
    vorname = models.CharField("Vorname", max_length=100)
    nachname = models.CharField("Nachname", max_length=100)

    email = models.EmailField(blank=True)
    telefon = models.CharField('Telefonnummer', max_length=50, blank=True)

    notiz = models.TextField("Notiz", blank=True)
    aktiv = models.BooleanField(default=True)
    erstellt_am = models.DateTimeField(auto_now_add=True)
    geaendert_am = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vorname} {self.nachname} - {self.email}"
    
    class Meta:
        verbose_name = "Ansprechpartner"
        verbose_name_plural = "Ansprechpartner"
        unique_together = ("vorname", "nachname", "email")
        ordering = ["nachname", "vorname"]