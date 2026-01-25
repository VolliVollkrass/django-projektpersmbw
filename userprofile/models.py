from django.db import models
from django.contrib.auth.models import User

BERUFSGRUPPE = [
    ("di", "Diakon*innen"),
    ("pf", "Pfarrer*innen"),
    ("tp", "Pädergog*innen"),
    ("rel", "Religionspädergog*innen"),
    ("mu", "Kirchenmusiker*innen"),

    ]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    berufsgruppe = models.CharField(max_length=50, choices=BERUFSGRUPPE)
    stellenkuerzel = models.CharField(max_length=10)
    dienst_beendet = models.DateField(blank=True, null=True)
    bemerkung = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.user.email}"