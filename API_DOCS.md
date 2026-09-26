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

Request (`application/x-www-form-urlencoded`):

Beispiel-Felder:

- `username=admin@example.com`
- zusätzlich das konfigurierte Passwortfeld `password`

Die Anmeldung validiert gegen Benutzer in der Datenbank. Für lokale Entwicklung kann ein initialer Admin über `BOOTSTRAP_ADMIN_*` beim Start angelegt werden.

### `GET /api/v1/auth/me`

Liefert den aktuell authentifizierten Benutzer inklusive Rolle für Frontend-Rechteprüfung und Navigation.

## Fachmodule

Die folgenden Module sind als strukturierte Einstiegspunkte vorhanden:

- `GET /api/v1/properties/`
- `POST /api/v1/properties/`
- `GET /api/v1/properties/{property_id}`
- `PUT /api/v1/properties/{property_id}`
- `DELETE /api/v1/properties/{property_id}`
- `GET /api/v1/tenants/`
- `POST /api/v1/tenants/`
- `GET /api/v1/tenants/{tenant_id}`
- `PUT /api/v1/tenants/{tenant_id}`
- `DELETE /api/v1/tenants/{tenant_id}`
- `GET /api/v1/units/`
- `POST /api/v1/units/`
- `GET /api/v1/units/{unit_id}`
- `PUT /api/v1/units/{unit_id}`
- `DELETE /api/v1/units/{unit_id}`
- `GET /api/v1/contracts/`
- `POST /api/v1/contracts/`
- `GET /api/v1/contracts/{contract_id}`
- `PUT /api/v1/contracts/{contract_id}`
- `DELETE /api/v1/contracts/{contract_id}`
- `GET /api/v1/invoices/`
- `POST /api/v1/invoices/`
- `GET /api/v1/invoices/{invoice_id}`
- `PUT /api/v1/invoices/{invoice_id}`
- `DELETE /api/v1/invoices/{invoice_id}`
- `GET /api/v1/payments/`
- `POST /api/v1/payments/`
- `GET /api/v1/payments/{payment_id}`
- `PUT /api/v1/payments/{payment_id}`
- `DELETE /api/v1/payments/{payment_id}`
- `GET /api/v1/banking/`
- `POST /api/v1/banking/transactions`
- `GET /api/v1/banking/transactions/{transaction_id}`
- `PUT /api/v1/banking/transactions/{transaction_id}`
- `DELETE /api/v1/banking/transactions/{transaction_id}`
- `POST /api/v1/banking/transactions/{transaction_id}/match-payment`
- `POST /api/v1/banking/import-stub`
- `GET /api/v1/documents/`
- `POST /api/v1/documents/upload`
- `GET /api/v1/documents/{document_id}`
- `POST /api/v1/documents/{document_id}/process-ocr`
- `POST /api/v1/documents/{document_id}/apply-ocr-to-invoice`
- `GET /api/v1/accounting/`
- `POST /api/v1/accounting/`
- `GET /api/v1/accounting/{entry_id}`
- `PUT /api/v1/accounting/{entry_id}`
- `DELETE /api/v1/accounting/{entry_id}`
- `GET /api/v1/reports/`

Der Reporting-Endpunkt liefert aktuell eine Dashboard-Zusammenfassung mit Zählern und Summen für Immobilien, Verträge, Rechnungen, Zahlungen und Accounting Entries.

Schreiboperationen sind aktuell auf die Rollen `owner` und `manager` beschränkt; `viewer` bleibt read-only.

Alle Antworten liefern im Initial-Setup einen statusorientierten Payload, damit die Endpunkte früh integrierbar sind und später schrittweise mit Geschäftslogik hinterlegt werden können.

## Dokumente und OCR

- Dokumente können aktuell zu `invoice` oder `property` hochgeladen werden.
- Der OCR-Endpunkt unterstützt aktuell pragmatisch:
  - PDF mit eingebettetem Text
  - JPG/JPEG/PNG per Bild-OCR
  - TXT als Entwicklungs-/Fallbackformat
- `POST /api/v1/documents/{document_id}/process-ocr` startet OCR jetzt asynchron und liefert `202 Accepted`.
- `POST /api/v1/documents/{document_id}/retry-ocr` startet fehlgeschlagene OCR-Läufe erneut.
- Dokumente enthalten OCR-Statusinformationen inkl. Fehlertext und Versuchszähler.
- Der OCR-Pfad extrahiert erste Rechnungsdaten wie Lieferant, Rechnungsnummer, Rechnungsdatum und Bruttobetrag.

## Nächste API-Schritte

1. CRUD-Endpunkte pro Fachmodul
2. Filter-, Such- und Pagination-Standards
3. Rollen- und Rechteprüfung
4. OpenAPI-Beispiele je Ressource
5. Upload- und Async-Endpunkte für Dokumente und OCR
