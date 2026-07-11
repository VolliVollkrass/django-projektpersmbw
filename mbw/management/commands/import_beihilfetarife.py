"""Beihilfesätze der Bayerischen Beamtenkrankenkasse einspielen.

Quelle: Beitragstabelle „Beiträge Beihilfeablöseversicherung und kirchliche
Höherversicherung ab 1.1.2026“ (BBK, SAP-Nr. 32 65 02). Die Tabelle kommt
jährlich per Post/PDF; neue Jahre hier ergänzen oder im Admin pflegen.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from mbw.models import Beihilfesatz

# Jahr -> Tarif -> Liste (alter_bis, satz); alter_bis None = keine Obergrenze,
# "kind" = Kindersatz
TARIFE = {
    2026: {
        Beihilfesatz.Tarif.T814: {
            "erwachsen": [(66, "2.15"), (None, "12.95")],
            "kind": None,
        },
        Beihilfesatz.Tarif.T830: {
            "erwachsen": [
                (29, "145.06"),
                (39, "183.74"),
                (49, "210.93"),
                (59, "308.94"),
                (69, "468.55"),
                (79, "714.15"),
                (None, "1050.61"),
            ],
            "kind": "182.64",
        },
    },
}


class Command(BaseCommand):
    help = "Spielt die fest hinterlegten BBK-Beihilfesätze (Tarife 814/830) ein."

    @transaction.atomic
    def handle(self, *args, **options):
        anzahl = 0
        for jahr, tarife in TARIFE.items():
            for tarif, kategorien in tarife.items():
                for alter_bis, satz in kategorien["erwachsen"]:
                    Beihilfesatz.objects.update_or_create(
                        jahr=jahr,
                        tarif=tarif,
                        kategorie=Beihilfesatz.Kategorie.ERWACHSEN,
                        alter_bis=alter_bis,
                        defaults={"satz": Decimal(satz)},
                    )
                    anzahl += 1
                if kategorien["kind"]:
                    Beihilfesatz.objects.update_or_create(
                        jahr=jahr,
                        tarif=tarif,
                        kategorie=Beihilfesatz.Kategorie.KIND,
                        alter_bis=None,
                        defaults={"satz": Decimal(kategorien["kind"])},
                    )
                    anzahl += 1
        self.stdout.write(self.style.SUCCESS(f"{anzahl} Beihilfesätze eingespielt/aktualisiert."))
