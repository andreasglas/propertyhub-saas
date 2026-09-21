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

### Backend lokal

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

### Frontend lokal

```bash
cd frontend
npm ci
npm run dev
```

## Kernfunktionen des Grundgerüsts

- FastAPI App mit versionierter API-Struktur
- Konfigurationsmanagement via Pydantic Settings
- SQLAlchemy-Setup für PostgreSQL-kompatible Persistenz
- JWT-Sicherheitsbausteine und Dependency-Grundlagen
- Celery- und Redis-Grundstruktur für Hintergrundjobs
- React/Vite/MUI-Dashboard-Starter
- Zentrale API-Client-Abstraktion im Frontend

## Weiterführende Dokumentation

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
- [API_DOCS.md](API_DOCS.md)
