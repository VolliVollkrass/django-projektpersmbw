from django.db import models
from django.contrib.auth.models import User
from traeger.models import Stelle
from personal.models import Mitarbeiter
from decimal import Decimal


class Einsatz(models.Model):
    stelle = models.ForeignKey(Stelle, on_delete=models.CASCADE, related_name="einsaetze")

    mitarbeiter = models.ForeignKey(Mitarbeiter, on_delete=models.CASCADE, related_name="einsaetze")

    beginn = models.DateField()
    ende = models.DateField(null=True, blank=True)

    umfang = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("1.00"))

    abrechnung = models.BooleanField("Abrechnung über LKA", default=False)
    
    aktiv = models.BooleanField(default=True)
    bemerkung = models.TextField(blank=True)
    angelegt_von = models.ForeignKey(User, related_name="angelegte_stelle_mitarbeiter", on_delete=models.SET_NULL, null=True, blank=True)
    angelegt_am = models.DateTimeField(auto_now_add=True)
    aktualisiert_am = models.DateTimeField(auto_now=True)

    @property
    def umfang_prozent(self):
        return self.umfang * 100
    
    def __str__(self):
        return f"{self.stelle}, {self.mitarbeiter} Umfang:{self.umfang_prozent} von:{self.beginn} bis:{self.ende}"