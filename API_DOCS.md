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

## Audit-Log

### `GET /api/v1/audit-logs/`

Liefert den organisationsbezogenen Activity-Feed bzw. das Audit-Log. Optional filterbar über `resource_type`, `action` und `limit`.

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
- `GET /api/v1/tasks/`
- `POST /api/v1/tasks/`
- `GET /api/v1/tasks/templates`
- `POST /api/v1/tasks/templates`
- `PUT /api/v1/tasks/templates/{template_id}`
- `DELETE /api/v1/tasks/templates/{template_id}`
- `POST /api/v1/tasks/templates/generate-due`
- `GET /api/v1/tasks/{task_id}`
- `PUT /api/v1/tasks/{task_id}`
- `DELETE /api/v1/tasks/{task_id}`
- `GET /api/v1/tasks/{task_id}/comments`
- `POST /api/v1/tasks/{task_id}/comments`
- `GET /api/v1/tasks/{task_id}/attachments`
- `GET /api/v1/tasks/{task_id}/history`
- `GET /api/v1/vendors/`
- `POST /api/v1/vendors/`
- `PUT /api/v1/vendors/{vendor_id}`
- `DELETE /api/v1/vendors/{vendor_id}`
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
- `GET /api/v1/audit-logs/`
- `GET /api/v1/operating-costs/periods`
- `POST /api/v1/operating-costs/periods`
- `PUT /api/v1/operating-costs/periods/{period_id}`
- `DELETE /api/v1/operating-costs/periods/{period_id}`
- `GET /api/v1/operating-costs/periods/{period_id}/items`
- `POST /api/v1/operating-costs/periods/{period_id}/items`
- `POST /api/v1/operating-costs/periods/{period_id}/finalize`
- `GET /api/v1/operating-costs/periods/{period_id}/export.csv`
- `GET /api/v1/operating-costs/periods/{period_id}/export.pdf`
- `PUT /api/v1/operating-costs/items/{item_id}`
- `DELETE /api/v1/operating-costs/items/{item_id}`
- `GET /api/v1/operating-costs/periods/{period_id}/settlement-preview`

Der Reporting-Endpunkt liefert aktuell eine Dashboard-Zusammenfassung mit Zählern und Summen für Immobilien, Verträge, Rechnungen, Zahlungen und Accounting Entries. Zusätzlich gibt es jetzt eine offene-Posten-Liste sowie CSV-Exporte für Dashboard-Summary und offene Rechnungen.

Wichtige Mutationen in Organisation, Benutzerverwaltung, Stammdaten, Billing, Banking und Dokumentenworkflow werden zusätzlich im Audit-Log protokolliert.

Schreiboperationen sind aktuell auf die Rollen `owner` und `manager` beschränkt; `viewer` bleibt read-only.

Alle Antworten liefern im Initial-Setup einen statusorientierten Payload, damit die Endpunkte früh integrierbar sind und später schrittweise mit Geschäftslogik hinterlegt werden können.

## Aufgaben und Tickets

- Aufgaben sind mandantenfähig und können optional auf Immobilie und Einheit referenzieren.
- Aufgaben können zusätzlich einem Dienstleister sowie einer wiederkehrenden Vorlage zugeordnet werden.
- Unterstützte Kategorien sind aktuell `maintenance`, `inspection`, `tenant_request`, `accounting`, `compliance` und `other`.
- Status und Priorität werden organisationsbezogen verwaltet und im Audit-Log protokolliert.
- `GET /api/v1/tasks/{task_id}/comments` und `POST /api/v1/tasks/{task_id}/comments` bilden den Kommunikationsverlauf je Vorgang ab.
- `GET /api/v1/tasks/{task_id}/attachments` liefert aufgabenbezogene Dokumente aus dem bestehenden Dokumentenmodul.
- `GET /api/v1/tasks/{task_id}/history` kombiniert Audit-Events, Kommentare und Anhänge zu einer operativen Verlaufssicht.
- `GET /api/v1/tasks/templates` bis `DELETE /api/v1/tasks/templates/{template_id}` verwalten wiederkehrende Aufgabenmuster.
- `POST /api/v1/tasks/templates/generate-due` erzeugt fällige Aufgaben aus aktiven Vorlagen.
- Zusätzlich erzeugt ein täglicher Celery-Beat-Lauf fällige wiederkehrende Aufgaben automatisch für alle Organisationen mit aktiven Vorlagen.
- `viewer` kann Aufgaben lesen, aber nicht anlegen, aktualisieren oder löschen.

## Dienstleister

- Dienstleister sind mandantenfähig und dienen als Stammdaten für Handwerker, Servicepartner und externe Ansprechpartner.
- `GET /api/v1/vendors/`, `POST /api/v1/vendors/`, `PUT /api/v1/vendors/{vendor_id}` und `DELETE /api/v1/vendors/{vendor_id}` verwalten Name, Kategorie, Kontakt- und Notizdaten.
- Aufgaben können optional mit einem Dienstleister verknüpft werden, um Zuständigkeiten im Dashboard sichtbar zu machen.

## Nebenkosten und Betriebskosten

- Nebenkostenperioden sind immobilienbezogen und mandantenfähig.
- Positionen innerhalb einer Periode unterstützen aktuell die Umlageschlüssel `area`, `unit_count`, `occupancy_days` und `advance_share`.
- Die Abrechnungsvorschau berücksichtigt überlappende aktive Verträge, Teiljahreszeiträume, Leerstandstage, vorhandene Wohnflächen und hinterlegte Vorauszahlungen aus dem Mietvertrag.
- `GET /api/v1/operating-costs/periods/{period_id}/settlement-preview` liefert eine Vorschau je Vertrag/Wohneinheit mit Kostenanteil, geleisteter Vorauszahlung und Saldo.
- Leerstand wird in der Vorschau als eigene Zeile pro Einheit ausgewiesen.
- `POST /api/v1/operating-costs/periods/{period_id}/finalize` markiert eine Periode als finalisiert.
- `GET /api/v1/operating-costs/periods/{period_id}/export.csv` und `GET /api/v1/operating-costs/periods/{period_id}/export.pdf` exportieren die Betriebskostenabrechnung.

## Dokumente und OCR

- - Dokumente können aktuell zu `invoice`, `property` oder `task` hochgeladen werden.
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
