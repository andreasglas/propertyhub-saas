# API Dokumentation

## Basis

- Base URL lokal: `http://localhost:8000`
- API-Version: `/api/v1`
- Authentifizierung: JWT Access Token

## Systemendpunkte

### `GET /health`

Prüft die Erreichbarkeit des Backends.

### `GET /api/v1`

Liefert Metadaten zur API-Version.

## Auth

### `POST /api/v1/auth/token`

Erzeugt ein JWT für lokale Entwicklung oder spätere Login-Integrationen.

Request:

```json
{
  "email": "admin@example.com",
  "password": "change-me"
}
```

## Fachmodule

Die folgenden Module sind als strukturierte Einstiegspunkte vorhanden:

- `GET /api/v1/properties/`
- `GET /api/v1/tenants/`
- `GET /api/v1/units/`
- `GET /api/v1/contracts/`
- `GET /api/v1/invoices/`
- `GET /api/v1/banking/`
- `GET /api/v1/accounting/`
- `GET /api/v1/reports/`

Alle Antworten liefern im Initial-Setup einen statusorientierten Payload, damit die Endpunkte früh integrierbar sind und später schrittweise mit Geschäftslogik hinterlegt werden können.

## Nächste API-Schritte

1. CRUD-Endpunkte pro Fachmodul
2. Filter-, Such- und Pagination-Standards
3. Rollen- und Rechteprüfung
4. OpenAPI-Beispiele je Ressource
5. Upload- und Async-Endpunkte für Dokumente und OCR
