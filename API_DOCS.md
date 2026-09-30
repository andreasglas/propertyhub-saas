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

### `GET /api/v1/auth/invitations/{token}`

Liefert öffentliche Einladungsinformationen für den Passwort-Setup-Flow.

### `POST /api/v1/auth/setup-password`

Akzeptiert ein Einladungstoken und setzt das erste Passwort für einen eingeladenen Benutzer.

## Organisation

### `GET /api/v1/organization/me`

Liefert die aktuelle Organisation des eingeloggten Benutzers.

### `PUT /api/v1/organization/me`

Aktualisiert Organisationsdaten wie Name, Adresse und Kontaktdaten. Nur `owner`.

## Benutzerverwaltung

### `GET /api/v1/users/`

Listet alle Benutzer der aktuellen Organisation. Sichtbar für `owner` und `manager`.

### `POST /api/v1/users/`

Legt einen neuen Benutzer in der aktuellen Organisation an. Nur `owner`.

### `PUT /api/v1/users/{user_id}`

Aktualisiert Rolle, Aktivstatus, Name und optional Passwort eines Benutzers. Nur `owner`.

### `POST /api/v1/users/invitations`

Erstellt einen eingeladenen Benutzer ohne Passwort und liefert Setup-Link und absolute Setup-URL zurück. Wenn SMTP konfiguriert ist, wird direkt eine Einladungsmail versendet; andernfalls wird der Versandstatus als `manual` markiert. Nur `owner`.

### `POST /api/v1/users/{user_id}/invite`

Erzeugt für einen noch nicht aktivierten Benutzer einen neuen Einladungslink und triggert einen erneuten Mailversand bzw. manuellen Fallback. Nur `owner`.

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
- `GET /api/v1/invoices/overdue`
- `GET /api/v1/invoices/{invoice_id}`
- `GET /api/v1/invoices/{invoice_id}/reminders`
- `POST /api/v1/invoices/{invoice_id}/reminders`
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
- `POST /api/v1/banking/import`
- `POST /api/v1/banking/import-stub`
- `GET /api/v1/documents/`
- `POST /api/v1/documents/upload`
- `GET /api/v1/documents/{document_id}`
- `POST /api/v1/documents/{document_id}/process-ocr`
- `PATCH /api/v1/documents/{document_id}/review`
- `POST /api/v1/documents/{document_id}/apply-ocr-to-invoice`
- `GET /api/v1/accounting/`
- `POST /api/v1/accounting/`
- `GET /api/v1/accounting/{entry_id}`
- `PUT /api/v1/accounting/{entry_id}`
- `DELETE /api/v1/accounting/{entry_id}`
- `GET /api/v1/reports/`
- `GET /api/v1/reports/open-invoices`
- `GET /api/v1/reports/export/dashboard.csv`
- `GET /api/v1/reports/export/open-invoices.csv`

Der Reporting-Endpunkt liefert aktuell eine Dashboard-Zusammenfassung mit Zählern und Summen für Immobilien, Verträge, Rechnungen, Zahlungen und Accounting Entries. Zusätzlich gibt es jetzt eine offene-Posten-Liste sowie CSV-Exporte für Dashboard-Summary und offene Rechnungen.

Schreiboperationen sind aktuell auf die Rollen `owner` und `manager` beschränkt; `viewer` bleibt read-only.

Alle Antworten liefern im Initial-Setup einen statusorientierten Payload, damit die Endpunkte früh integrierbar sind und später schrittweise mit Geschäftslogik hinterlegt werden können.

## Dokumente und OCR

- Dokumente können aktuell zu `invoice` oder `property` hochgeladen werden.
- Dokumente enthalten jetzt zusätzlich Review-Metadaten wie Kategorie, Version, Freigabestatus, Kommentar und Reviewer.
- Der OCR-Endpunkt unterstützt aktuell pragmatisch:
  - PDF mit eingebettetem Text
  - JPG/JPEG/PNG per Bild-OCR
  - TXT als Entwicklungs-/Fallbackformat
- `POST /api/v1/documents/{document_id}/process-ocr` startet OCR jetzt asynchron und liefert `202 Accepted`.
- `POST /api/v1/documents/{document_id}/retry-ocr` startet fehlgeschlagene OCR-Läufe erneut.
- `PATCH /api/v1/documents/{document_id}/review` dient zur manuellen Nachbearbeitung und Freigabe von Dokumenten.
- Dokumente enthalten OCR-Statusinformationen inkl. Fehlertext und Versuchszähler.
- Für echte Hintergrundausführung nutzt OCR Celery mit Redis als Broker/Backend.
- Der OCR-Pfad extrahiert erste Rechnungsdaten wie Lieferant, Rechnungsnummer, Rechnungsdatum und Bruttobetrag.

## Neue operative Flows

1. SMTP-basierte Einladungsmails mit Versandstatus
2. CSV-/CAMT-Bankimport mit Dublettenprüfung
3. Offene Rechnungen, Fälligkeiten und Reminder-Historie
4. Dokumenten-Review und manuelle Nachbearbeitung
5. CSV-Exporte für operative Reports
