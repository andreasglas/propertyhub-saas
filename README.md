# PropertyHub SaaS

Professionelle, mandantenfähige SaaS-Plattform zur Verwaltung von Immobilien, Wohneinheiten, Mietverhältnissen, Rechnungen und Finanzprozessen.

## Zielsetzung

Dieses Repository enthält das initiale, produktionsnahe Grundgerüst für:

- ein Python/FastAPI-Backend
- ein React/TypeScript-Frontend mit Material UI
- lokale Entwicklungsumgebungen via Docker Compose
- Multi-Tenant-fähige Architekturbausteine
- Erweiterungspunkte für Banking, KI, Dokumente und Reporting

## Projektstruktur

```text
propertyhub-saas/
├── backend/
├── frontend/
├── docker-compose.yml
├── README.md
├── ARCHITECTURE.md
├── API_DOCS.md
└── DATABASE_SCHEMA.md
```

## Schnellstart

### Mit Docker Compose

```bash
cp .env.example .env
cp backend/.env.example backend/.env
docker compose up --build
```

Startet Backend, Frontend, PostgreSQL, Redis und einen Celery-Worker für OCR-Hintergrundjobs.

Alternativ per Python-Startskript:

```bash
python /home/runner/work/propertyhub-saas/propertyhub-saas/start_propertyhub.py
```

Im Hintergrund starten:

```bash
python /home/runner/work/propertyhub-saas/propertyhub-saas/start_propertyhub.py --detached
```

Das Skript erstellt bei Bedarf automatisch `.env` und `backend/.env` aus den Example-Dateien und zeigt dir danach die lokalen URLs an.

### Start-Checkliste

1. Docker Desktop oder Docker Engine mit `docker compose` muss laufen.
2. Optional in `/home/runner/work/propertyhub-saas/propertyhub-saas/backend/.env` `SECRET_KEY` und `BOOTSTRAP_ADMIN_PASSWORD` anpassen.
3. Starten mit:

   ```bash
   python /home/runner/work/propertyhub-saas/propertyhub-saas/start_propertyhub.py --detached
   ```

4. Danach öffnen:
   - Frontend: `http://localhost:5173`
   - Backend: `http://localhost:8000`
   - Swagger UI: `http://localhost:8000/docs`
5. Anmelden mit:
   - E-Mail: `admin@example.com`
   - Passwort: Wert aus `BOOTSTRAP_ADMIN_PASSWORD` in `backend/.env`

### Backend lokal

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Optional in separatem Terminal für echte OCR-Queue-Verarbeitung:

```bash
celery -A app.tasks.celery_app.celery_app worker --loglevel=info -Q propertyhub.default
```

### Frontend lokal

```bash
cd frontend
npm ci
npm run dev
```

Das Frontend nutzt im Development standardmäßig den relativen Pfad `/api`; lokal übernimmt Vite das Proxying auf das Backend.

## Kernfunktionen des Grundgerüsts

- FastAPI App mit versionierter API-Struktur
- Konfigurationsmanagement via Pydantic Settings
- SQLAlchemy-Setup für PostgreSQL-kompatible Persistenz
- JWT-Sicherheitsbausteine mit DB-basierter Benutzer-Authentifizierung
- Celery- und Redis-Grundstruktur für Hintergrundjobs
- React/Vite/MUI-Dashboard-Starter
- Zentrale API-Client-Abstraktion im Frontend
- erster Dokumenten- und OCR-Testpfad für Rechnungsbelege
- nutzbare Frontend-Bereiche für Immobilien, Einheiten, Mieter, Verträge, Billing, Banking und Dokumente
- Admin-Bereiche für Organisationsdaten und Benutzerverwaltung mit Rollensteuerung
- Einladungs- und Passwort-Setup-Flow für neue Benutzer
- SMTP-fähiger Einladungsversand mit Versandstatus und manuellem Fallback ohne Mailserver
- CSV-/CAMT-Bankimport mit Dublettenprüfung und erster automatischer Zahlungszuordnung
- Fälligkeiten, offene Posten, Reminder-Historie und CSV-Reporte für Rechnungen
- Dokumenten-Review mit Kategorie-, Versions- und Freigabe-Metadaten
- Audit-Log für wichtige Mutationen sowie Activity-Feed im Dashboard
- standardisierte Suche-, Filter- und Pagination-Muster für operative Listen im Dashboard

## Erweiterte Backend-Konfiguration

Für echte Einladungsmails und Zahlungserinnerungen können in `/home/runner/work/propertyhub-saas/propertyhub-saas/backend/.env` SMTP-Daten gesetzt werden:

```env
FRONTEND_APP_URL=http://localhost:5173
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=mailer@example.com
SMTP_PASSWORD=replace-me
SMTP_FROM_EMAIL=mailer@example.com
SMTP_FROM_NAME=PropertyHub
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

Ohne SMTP bleibt der Invite-/Reminder-Flow lokal nutzbar und markiert Sendungen automatisch als `manual`.

## Weiterführende Dokumentation

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
- [API_DOCS.md](API_DOCS.md)
