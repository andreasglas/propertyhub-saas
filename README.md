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

## 📱 Auf dem iPhone / mobil öffnen

1. Einmalig im Repository **Settings → Pages → Build and deployment → Source: GitHub Actions** auswählen.
2. Nach dem Merge auf `main` läuft bei jedem Push automatisch der Workflow **Deploy frontend to GitHub Pages**. Er kann auch unter **Actions → Run workflow** manuell gestartet werden.
3. Nach erfolgreichem Deployment in Safari öffnen: **https://andreasglas.github.io/propertyhub-saas/**
4. Für die Installation auf dem iPhone: **Safari → Teilen → „Zum Home-Bildschirm“ → Hinzufügen**. Ein lokaler Server oder Computer ist dafür nicht nötig.

Die PWA speichert die App-Oberfläche für spätere Offline-Aufrufe. Im normalen Betrieb benötigen Anmeldung, Geschäftsdaten und Änderungen eine Verbindung zum Backend; API-Antworten werden nicht offline gespeichert. Im Demo-Modus liegen alle Daten lokal im Browser.

**Wichtig:** GitHub Pages hostet nur das statische Frontend, nicht das FastAPI-Backend. Der Pages-Build läuft deshalb standardmäßig im **Demo-Modus** (siehe unten): Anmeldung und alle Bereiche funktionieren mit fiktiven Beispieldaten komplett ohne Backend.

Für ein separat gehostetes Backend unter **Settings → Secrets and variables → Actions → Variables** die Repository-Variable `VITE_DEMO_MODE=false` und zusätzlich `VITE_API_BASE_URL` setzen, z. B. `https://api.example.com/api`. Die URL muss HTTPS verwenden; das Backend muss CORS für `https://andreasglas.github.io` erlauben. Danach den Workflow erneut starten: Vite übernimmt den Wert beim Build. Der Wert ist öffentlich im JavaScript sichtbar und darf keine Secrets enthalten.

Lokal lässt sich derselbe Wert beim Build setzen:

```bash
cd frontend
VITE_API_BASE_URL=https://api.example.com/api npm run build
```

Ohne Konfiguration bleibt `/api` der Standard für den lokalen Vite-Proxy. Der lokale Dev-Server bleibt unter `http://localhost:5173/` erreichbar; nur Produktionsbuilds verwenden den GitHub-Pages-Subpath. Für Einladungslinks des separat gehosteten Backends `FRONTEND_APP_URL=https://andreasglas.github.io/propertyhub-saas` setzen.

## 🧪 Demo-Modus (ohne Backend)

Der Demo-Modus macht die komplette Oberfläche ohne laufendes Backend testbar – z. B. auf dem iPhone über GitHub Pages. Alle API-Aufrufe des zentralen API-Clients (`frontend/src/services/apiClient.ts`) werden dann lokal im Browser von einem Mock-Backend (`frontend/src/demo/`) beantwortet; es findet **kein** Netzwerkzugriff auf eine API statt.

**Aktivierung:** ausschließlich über das Build-Flag `VITE_DEMO_MODE=true`. Jeder andere Wert (oder kein Wert) bedeutet normalen Backendbetrieb mit echter Authentifizierung; der Demo-Code ist in normalen Builds nicht enthalten. Backendfehler fallen nie still auf Demo-Daten zurück. Der Pages-Workflow setzt `VITE_DEMO_MODE` standardmäßig auf `true` (abschaltbar über die Repository-Variable `VITE_DEMO_MODE=false`).

**Öffentliche Demo-Zugangsdaten** (fiktiv, auch auf der Login-Seite angezeigt und vorausgefüllt):

| E-Mail | Passwort | Rolle |
| --- | --- | --- |
| `demo@propertyhub.example` | `demo1234` | Owner – Vollzugriff inkl. Organisation & Benutzerverwaltung |
| `manager@propertyhub.example` | `demo1234` | Manager – Stammdaten & Vorgänge bearbeiten |
| `viewer@propertyhub.example` | `demo1234` | Viewer – nur lesen |

Eine Beispiel-Einladung lässt sich unter `/setup-password?token=demo-invite-nina` öffnen.

**Lokal nutzen:**

```bash
cd frontend
npm ci
VITE_DEMO_MODE=true npm run dev        # http://localhost:5173/
# oder statischen Build wie auf Pages prüfen:
VITE_DEMO_MODE=true npm run build && npm run preview   # http://localhost:4173/propertyhub-saas/
```

**Auf dem iPhone testen:** Nach dem Deployment **https://andreasglas.github.io/propertyhub-saas/** in Safari öffnen, mit `demo@propertyhub.example` / `demo1234` anmelden und über das Menü (☰) durch alle Bereiche navigieren. Unterseiten lassen sich direkt aufrufen und neu laden (über das vorhandene `404.html`-Weiterleitungskonzept).

**Daten & Zurücksetzen:** Beispieldaten (Immobilien, Einheiten, Mieter, Verträge, Rechnungen, Zahlungen, Banking, Buchhaltung, Betriebskosten, Aufgaben inkl. Vorlagen/Kommentaren, Dokumente, Berichte, Organisation, Benutzer, Dienstleister, Audit-Log) sind miteinander verknüpft und enthalten verschiedene Status. Änderungen werden versioniert im `localStorage` unter eigenen Schlüsseln (`propertyhub.demo.data.v1`, Sitzung: `propertyhub.demo.auth.session`) gespeichert – getrennt vom normalen Login-Schlüssel. Der Button **„Demo-Daten zurücksetzen“** im Demo-Hinweis stellt den Ausgangszustand wieder her.

**Grenzen des Demo-Modus:**

- Alle Daten sind fiktiv und existieren nur in diesem Browser; es gibt keine Produktivwirkung und keine Synchronisation zwischen Geräten.
- E-Mails (Einladungen) werden nicht versendet; Einladungslinks funktionieren nur im selben Browser.
- Bankimport und OCR sind Simulationen (OCR läuft wenige Sekunden; Dateinamen mit „unscharf“ schlagen beim ersten Versuch fehl, um „Erneut versuchen“ zu zeigen).
- Hochgeladene Dateien verlassen das Gerät nicht; gespeichert werden nur Dateiname und Metadaten.
- Passwörter werden nicht gespeichert; alle Demo-Konten nutzen `demo1234`.
- Operationen, die das Mock-Backend nicht kennt, werden mit einer verständlichen Meldung („Diese Funktion ist im Demo-Modus nicht verfügbar.“) abgelehnt, statt eine Netzwerkanfrage auszulösen.

**Tests:** `cd frontend && npm test` (Vitest) prüft Aktivierung/Abgrenzung, Demo-Login/Logout/Reload, repräsentative CRUD-Flows, Rollen und dass im Demo-Modus keine Backend-Requests stattfinden.

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
- Nebenkostenperioden und Betriebskostenpositionen pro Immobilie mit Verteilungsvorschau nach Fläche oder Einheit
- finale Nebenkostenabrechnung mit CSV-/PDF-Export, erweiterten Umlageschlüsseln sowie Leerstands-/Teiljahreslogik
- Aufgaben- und Ticketmodul für Wartungen, Prüfungen und operative Vorgänge mit Objekt-/Einheitenbezug
- Dienstleisterverwaltung für Handwerker und Servicepartner mit Aufgaben-Zuordnung
- Aufgabenkommentare, Historie und Dokumentanhänge für echte Wartungs-Workflows
- wiederkehrende Aufgabenvorlagen mit manueller Erzeugung fälliger Vorgänge
- automatisierte Erzeugung fälliger wiederkehrender Aufgaben per Celery Beat Scheduler
- geplante/tatsächliche Task-Kosten sowie Abschlusszeitpunkt und Abschlussnotizen im Wartungsworkflow
- CSV-Aufgabenreport mit Status-, Fälligkeits- und Kostenübersicht für operative Steuerung
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

Für automatische wiederkehrende Aufgaben kann der Scheduler in `/home/runner/work/propertyhub-saas/propertyhub-saas/backend/.env` gesteuert werden:

```env
RECURRING_TASK_GENERATION_ENABLED=true
RECURRING_TASK_GENERATION_HOUR=6
RECURRING_TASK_GENERATION_MINUTE=0
```

Im Docker-Setup läuft dafür zusätzlich der `scheduler`-Service mit Celery Beat.

## Weiterführende Dokumentation

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
- [API_DOCS.md](API_DOCS.md)
