# Deployment: diakon.undmeererleben.de

Zielumgebung: Hetzner CX23, Ubuntu, Traefik v2.11 (`traefik-proxy`-Netzwerk),
geteilter PostgreSQL-16-Container (`postgres`). Wildcard-DNS ist aktiv —
kein DNS-Eintrag nötig.

## 1. Datenbank anlegen (einmalig, auf dem Server)

```bash
docker exec -it postgres psql -U admin -d postgres
```

```sql
CREATE DATABASE diakon;
CREATE USER diakon_user WITH PASSWORD '<SICHERES_PASSWORT>';
GRANT ALL PRIVILEGES ON DATABASE diakon TO diakon_user;
ALTER DATABASE diakon OWNER TO diakon_user;
\q
```

(`ALTER DATABASE ... OWNER` ist bei Postgres 16 nötig, damit der User im
Schema `public` Tabellen anlegen darf.)

## 2. Projekt auf den Server bringen

```bash
mkdir -p ~/docker/diakon
cd ~/docker/diakon
git clone https://github.com/VolliVollkrass/django-projektpersmbw.git app
cp app/docker-compose.prod.yml docker-compose.yml
mkdir -p media
```

## 3. .env anlegen (~/docker/diakon/.env)

```bash
cp app/.env.example .env
nano .env
```

Ausfüllen:

```
DEBUG=False
SECRET_KEY=<NEUEN Key erzeugen, NICHT den lokalen verwenden>
ALLOWED_HOSTS=diakon.undmeererleben.de
CSRF_TRUSTED_ORIGINS=https://diakon.undmeererleben.de
DB_NAME=diakon
DB_USER=diakon_user
DB_PASSWORD=<Passwort aus Schritt 1>
DB_HOST=postgres
DB_PORT=5432
```

Neuen SECRET_KEY erzeugen:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

## 4. Starten

```bash
cd ~/docker/diakon
docker compose up -d --build
docker compose logs -f   # migrate + collectstatic + gunicorn beobachten
```

Danach erreichbar unter https://diakon.undmeererleben.de
(erstes Zertifikat kann ~30 Sekunden dauern).

Admin-Benutzer anlegen:

```bash
docker compose exec web python manage.py createsuperuser
```

## 5. Bestehende Daten aus der lokalen SQLite übernehmen (optional)

Auf dem Mac (im Projektordner, venv aktiv):

```bash
python manage.py dumpdata \
  --natural-foreign --natural-primary \
  -e contenttypes -e auth.permission -e sessions -e admin.logentry -e axes \
  -o dump.json
scp dump.json volker@46.224.226.138:~/docker/diakon/app/
```

Auf dem Server:

```bash
cd ~/docker/diakon
docker compose exec web python manage.py loaddata dump.json
rm app/dump.json   # danach löschen, enthält Personendaten!
```

## 6. Updates einspielen

```bash
cd ~/docker/diakon/app && git pull
cd ~/docker/diakon && docker compose up -d --build
```

## 6a. Benutzergruppen / Rollen

Einmalig (und nach Rollen-Änderungen erneut) ausführen:

```bash
docker compose exec web python manage.py setup_rollen
```

Legt drei Gruppen an:

| Gruppe | darf |
|---|---|
| Lesen | alles ansehen, nichts ändern |
| Sachbearbeitung | ansehen, anlegen, ändern – **nicht** löschen |
| Administration | alles inkl. löschen |

Benutzer im Django-Admin unter **Benutzer → Gruppen** zuordnen. Neue
Kollegen-Konten dort anlegen (nicht als Superuser!) und genau einer
Gruppe zuweisen.

## 7. Backup (täglich, Cron auf dem Server)

Script `~/docker/diakon/backup.sh`:

```bash
#!/bin/bash
set -e
BACKUP_DIR=~/backups/diakon
mkdir -p "$BACKUP_DIR"
STAMP=$(date +%F)
docker exec postgres pg_dump -U admin diakon | gzip > "$BACKUP_DIR/db_$STAMP.sql.gz"
tar czf "$BACKUP_DIR/media_$STAMP.tar.gz" -C ~/docker/diakon media
# Backups älter als 30 Tage löschen
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
```

Einrichten:

```bash
chmod +x ~/docker/diakon/backup.sh
crontab -e
# Zeile ergänzen: täglich 03:15 Uhr
15 3 * * * ~/docker/diakon/backup.sh
```

Wichtig: Die Backups liegen damit auf demselben Server. Für echte Sicherheit
zusätzlich auf eine Hetzner Storage Box oder den Mac synchronisieren.

## Hinweise

- Media-Dateien (Beurteilungs-/Rechnungs-PDFs) werden über eine
  login-geschützte Django-View ausgeliefert, nicht öffentlich.
- Login ist mit django-axes geschützt (5 Fehlversuche → 1 h Sperre).
  Sperre manuell aufheben: `docker compose exec web python manage.py axes_reset`
- Statics liefert WhiteNoise direkt aus dem Container.
