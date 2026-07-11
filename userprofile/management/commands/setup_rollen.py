from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

# Fachmodelle, auf die sich die Rollen beziehen
FACHMODELLE = [
    ("personal", "mitarbeiter"),
    ("ansprechpartner", "ansprechpartner"),
    ("traeger", "traeger"),
    ("traeger", "einrichtung"),
    ("traeger", "stelle"),
    ("einsatz", "einsatz"),
    ("mbw", "innenauftrag"),
    ("mbw", "quartalsabrechnung"),
    ("mbw", "fakturierungsvorgang"),
    ("mbw", "debitor"),
    ("mbw", "besoldungstabelle"),
    ("mbw", "besoldungsbetrag"),
    ("mbw", "familienzuschlagtabelle"),
    ("mbw", "familienzuschlagzeile"),
    ("mbw", "fzkindererhoehung"),
    ("mbw", "zulagensatz"),
    ("mbw", "beihilfesatz"),
    ("mbw", "mietenstufe"),
    ("mbw", "personalkostenimport"),
    ("mbw", "personalkostenzeile"),
    ("beurteilung", "supervisor"),
    ("beurteilung", "evaluationrequest"),
    ("beurteilung", "evaluation"),
]

ROLLEN = {
    "Lesen": ("view",),
    "Sachbearbeitung": ("view", "add", "change"),
    "Administration": ("view", "add", "change", "delete"),
}


class Command(BaseCommand):
    help = (
        "Legt die Benutzergruppen Lesen / Sachbearbeitung / Administration an "
        "bzw. setzt deren Berechtigungen zurück. Mehrfach ausführbar."
    )

    def handle(self, *args, **options):
        for rolle, aktionen in ROLLEN.items():
            group, created = Group.objects.get_or_create(name=rolle)
            perms = []
            for app_label, model in FACHMODELLE:
                ct = ContentType.objects.get(app_label=app_label, model=model)
                for aktion in aktionen:
                    perms.append(
                        Permission.objects.get(
                            content_type=ct, codename=f"{aktion}_{model}"
                        )
                    )
            group.permissions.set(perms)
            status = "angelegt" if created else "aktualisiert"
            self.stdout.write(
                self.style.SUCCESS(
                    f"Gruppe '{rolle}' {status} ({len(perms)} Berechtigungen)"
                )
            )
        self.stdout.write(
            "Fertig. Benutzer im Admin unter 'Benutzer' den Gruppen zuordnen."
        )
