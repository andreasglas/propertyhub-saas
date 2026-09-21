# Datenbankschema

## Überblick

Das initiale Schema bildet die Kernbereiche einer mandantenfähigen Immobilienverwaltungsplattform ab.

## ER-Diagramm

```mermaid
erDiagram
    USER {
        string id PK
        string email
        string full_name
        string role
        boolean is_active
    }

    PROPERTY {
        string id PK
        string organization_id
        string name
        string property_type
        string city
        string postal_code
    }

    UNIT {
        string id PK
        string organization_id
        string property_id FK
        string name
        string status
        float area_sqm
    }

    TENANT {
        string id PK
        string organization_id
        string first_name
        string last_name
        string email
    }

    CONTRACT {
        string id PK
        string organization_id
        string unit_id FK
        string tenant_id FK
        date start_date
        date end_date
        numeric cold_rent
    }

    INVOICE {
        string id PK
        string organization_id
        string property_id FK
        string vendor_name
        string invoice_number
        numeric gross_amount
        string status
    }

    PAYMENT {
        string id PK
        string organization_id
        string invoice_id FK
        string contract_id FK
        numeric amount
        date booking_date
    }

    ACCOUNTING_ENTRY {
        string id PK
        string organization_id
        string property_id FK
        string entry_type
        numeric amount
        date booking_date
    }

    DOCUMENT {
        string id PK
        string organization_id
        string related_model
        string related_id
        string document_type
        string file_name
    }

    PROPERTY ||--o{ UNIT : contains
    UNIT ||--o{ CONTRACT : assigned_to
    TENANT ||--o{ CONTRACT : signs
    PROPERTY ||--o{ INVOICE : receives
    INVOICE ||--o{ PAYMENT : settles
    CONTRACT ||--o{ PAYMENT : references
    PROPERTY ||--o{ ACCOUNTING_ENTRY : posts
```

## Tabellen

### users

- Benutzerverwaltung für Eigentümer, Hausverwaltungen, Steuerberater, Mitarbeiter
- vorbereitet für JWT, OAuth2 und spätere SSO-Erweiterungen

### properties

- Stammdaten zu Immobilien
- vorbereitet für Wohn- und Gewerbeeinheiten sowie steuerrelevante Merkmale

### units

- einzelne vermietbare Einheiten
- Zuordnung zu genau einer Immobilie

### tenants

- Mieterstammdaten und Kontaktinformationen

### contracts

- Mietvertragsdaten inklusive Mietbeginn, Mietende, Kaltmiete und Nebenkostenvorauszahlung

### invoices

- Eingangsrechnungen inkl. Lieferant, Rechnungsnummer, Betrag und Status

### payments

- Bank- und Zahlungsereignisse zur Zuordnung auf Rechnungen und Verträge

### accounting_entries

- vorbereitete Buchungsstruktur für Reporting, DATEV-Exporte und Steuerlogik

### documents

- Metadaten für revisionssichere Dokumentenablage

## Multi-Tenant-Konzept

Alle fachlichen Tabellen enthalten ein `organization_id`-Feld als Grundlage für:

- logische Mandantentrennung
- Filterung auf Datenbank- und Service-Ebene
- spätere Sicherheitsregeln und Audits
