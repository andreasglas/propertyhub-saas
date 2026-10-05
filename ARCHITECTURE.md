# Architekturübersicht

## 1. Zielbild

PropertyHub ist als modulare, mandantenfähige SaaS-Plattform für Privatvermieter, Hausverwaltungen und weitere Rollen im deutschen Immobilienumfeld konzipiert.

## 2. Architekturprinzipien

- **Multi-Tenant by design**: fachliche Daten werden strikt tenant-separiert
- **API-first**: Frontend, Integrationen und Hintergrundprozesse nutzen dieselbe Backend-API
- **Modulare Domänenstruktur**: Immobilien, Mieter, Verträge, Rechnungen, Banking, Reporting und KI sind getrennte Module
- **Asynchron erweiterbar**: OCR, Banking-Importe und Benachrichtigungen laufen über Celery-Tasks
- **Cloud-ready**: Docker- und Compose-Setup als Basis für Azure/Kubernetes-Deployments

## 3. High-Level-Komponenten

### Frontend

- React + TypeScript + Vite
- Material UI als Design-System
- API-Client für Backend-Kommunikation
- später erweiterbar um Auth-Flow, Rollensteuerung und Offline-States

### Backend

- FastAPI als API-Layer
- SQLAlchemy 2.x für ORM und Datenzugriff
- Pydantic für Validierung und Settings
- JWT/OAuth2-Grundlagen für Authentifizierung
- Celery + Redis für Hintergrundjobs

### Datenhaltung

- PostgreSQL als primäre relationale Datenbank
- Redis für Queueing, Caching und verteilte Tasks
- Dokumentenspeicher später über Blob/Object Storage erweiterbar

## 4. Modulstruktur Backend

- `core/`: Security, Dependencies, Exceptions
- `api/v1/endpoints/`: versionierte Endpunkte pro Fachmodul
- `db/models/`: ORM-Modelle
- `schemas/`: API-Schemas
- `services/`: Geschäftslogik
- `ml/`: KI-nahe Komponenten wie OCR, Matching, Forecasting
- `tasks/`: asynchrone Jobs
- `utils/`: Logging, Validatoren, Helfer

## 5. Mandantenfähigkeit

Mandantentrennung wird im Grundgerüst durch ein gemeinsames `organization_id`-Feld in fachlichen Basismodellen vorbereitet. In späteren Phasen folgen:

- Row-Level Security bzw. strikte Query-Filter
- Rollen- und Rechtekonzept
- Audit-Trails und Datenschutzfunktionen

## 6. Sicherheitskonzept

- JWT-basierte API-Authentifizierung
- Passwort-Hashing via Passlib/Bcrypt
- Secret- und Umgebungsvariablensteuerung
- zentrale Exception-Behandlung
- CORS-Konfiguration für getrennte Frontend-/Backend-Deployments

## 7. Betriebsmodell

### Lokale Entwicklung

- `docker compose up --build`
- Hot Reload für Backend und Frontend
- PostgreSQL und Redis als lokale Services

### Zielbetrieb

- Containerisierte Deployments
- Reverse Proxy / Ingress
- Managed PostgreSQL
- Managed Redis
- Object Storage für Dokumente
- Observability über strukturierte Logs und Metriken

## 8. Erweiterungspfad

Nächste Phasen bauen typischerweise auf diesem Grundgerüst auf:

1. Alembic-Migrationen und initiales Datenbankschema
2. echte CRUD-Workflows für Kernmodule
3. Auth mit Google/Microsoft/OAuth2-Flows
4. Dokumentenmanagement und OCR-Pipelines
5. Banking-Integrationen
6. Reporting, DATEV-Export und deutsche Steuerlogik
