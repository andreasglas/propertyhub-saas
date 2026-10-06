import type { AccountingEntry } from "../services/accountingService";
import type { AuditLogEntry } from "../services/auditLogService";
import type { BankTransaction } from "../services/bankingService";
import type { Contract } from "../services/contractService";
import type { DocumentRecord } from "../services/documentService";
import type { Invoice } from "../services/invoiceService";
import type { OperatingCostItem, OperatingCostPeriod } from "../services/operatingCostService";
import type { Organization } from "../services/organizationService";
import type { Payment } from "../services/paymentService";
import type { Property } from "../services/propertyService";
import type { TaskComment, TaskItem, TaskTemplate } from "../services/taskService";
import type { Tenant } from "../services/tenantService";
import type { Unit } from "../services/unitService";
import type { ManagedUser } from "../services/userAdminService";
import type { Vendor } from "../services/vendorService";
import { DEMO_DATA_VERSION } from "./demoConfig";

export type DemoUser = ManagedUser & {
  invitation_token?: string | null;
};

/** Gesamter Demo-Datenbestand. Alle Datensätze nutzen die Typen der echten Services. */
export type DemoState = {
  version: number;
  seeded_at: string;
  sequence: number;
  organization: Organization;
  users: DemoUser[];
  properties: Property[];
  units: Unit[];
  tenants: Tenant[];
  contracts: Contract[];
  invoices: Invoice[];
  payments: Payment[];
  bank_transactions: BankTransaction[];
  accounting_entries: AccountingEntry[];
  operating_cost_periods: OperatingCostPeriod[];
  operating_cost_items: OperatingCostItem[];
  vendors: Vendor[];
  tasks: TaskItem[];
  task_comments: TaskComment[];
  task_templates: TaskTemplate[];
  documents: DocumentRecord[];
  audit_logs: AuditLogEntry[];
  /** Simulierte OCR-Jobs: Dokument-ID → Zeitpunkt der Einreihung (ISO). */
  ocr_jobs: Record<string, string>;
};

export const DEMO_ORGANIZATION_ID = "demo-org-0001";
export const DEMO_OWNER_ID = "demo-user-owner";

const DAY_MS = 24 * 60 * 60 * 1000;

function toIsoDate(date: Date) {
  return date.toISOString().slice(0, 10);
}

/** Liefert Datumshelfer relativ zum Seed-Zeitpunkt, damit Fälligkeiten realistisch bleiben. */
export function createDateHelpers(now: Date) {
  const today = new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()));
  return {
    today,
    day(offsetDays: number) {
      return toIsoDate(new Date(today.getTime() + offsetDays * DAY_MS));
    },
    month(offsetMonths: number, dayOfMonth: number) {
      return toIsoDate(
        new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth() + offsetMonths, dayOfMonth)),
      );
    },
    timestamp(offsetDays: number, hour = 9, minute = 0) {
      const base = new Date(today.getTime() + offsetDays * DAY_MS);
      base.setUTCHours(hour, minute, 0, 0);
      return base.toISOString();
    },
    year: today.getUTCFullYear(),
  };
}

const ORG = DEMO_ORGANIZATION_ID;

export function createDemoSeed(now: Date = new Date()): DemoState {
  const { day, month, timestamp, year } = createDateHelpers(now);
  const previousYear = year - 1;

  const organization: Organization = {
    id: ORG,
    name: "Musterverwaltung Nord (Demo)",
    legal_name: "Musterverwaltung Nord GmbH – fiktive Demo-Organisation",
    street: "Beispielweg 1",
    postal_code: "20095",
    city: "Hamburg",
    country: "Deutschland",
    contact_email: "kontakt@propertyhub.example",
    contact_phone: "+49 40 555 0100",
  };

  const users: DemoUser[] = [
    {
      id: DEMO_OWNER_ID,
      organization_id: ORG,
      email: "demo@propertyhub.example",
      full_name: "Dana Demo",
      role: "owner",
      is_active: true,
      invitation_sent_at: timestamp(-400),
      invitation_accepted_at: timestamp(-399),
    },
    {
      id: "demo-user-manager",
      organization_id: ORG,
      email: "manager@propertyhub.example",
      full_name: "Max Manager",
      role: "manager",
      is_active: true,
      invitation_sent_at: timestamp(-200),
      invitation_accepted_at: timestamp(-198),
    },
    {
      id: "demo-user-viewer",
      organization_id: ORG,
      email: "viewer@propertyhub.example",
      full_name: "Vera Viewer",
      role: "viewer",
      is_active: true,
      invitation_sent_at: timestamp(-90),
      invitation_accepted_at: timestamp(-89),
    },
    {
      id: "demo-user-invited",
      organization_id: ORG,
      email: "neu@propertyhub.example",
      full_name: "Nina Neu",
      role: "manager",
      is_active: false,
      invitation_sent_at: timestamp(-2),
      invitation_accepted_at: null,
      invitation_token: "demo-invite-nina",
    },
    {
      id: "demo-user-inactive",
      organization_id: ORG,
      email: "ehemalig@propertyhub.example",
      full_name: "Erik Ehemalig",
      role: "viewer",
      is_active: false,
      invitation_sent_at: timestamp(-500),
      invitation_accepted_at: timestamp(-499),
    },
  ];

  const properties: Property[] = [
    {
      id: "demo-prop-lindenhof",
      organization_id: ORG,
      name: "Lindenhof 12",
      property_type: "residential",
      street: "Lindenstraße 12",
      postal_code: "20095",
      city: "Hamburg",
      purchase_price: 1250000,
    },
    {
      id: "demo-prop-kontorhaus",
      organization_id: ORG,
      name: "Kontorhaus am Hafen",
      property_type: "commercial",
      street: "Hafenallee 5",
      postal_code: "20457",
      city: "Hamburg",
      purchase_price: 2400000,
    },
    {
      id: "demo-prop-parkhaus",
      organization_id: ORG,
      name: "Parkhaus Elbblick",
      property_type: "parking",
      street: "Elbuferweg 88",
      postal_code: "22763",
      city: "Hamburg",
      purchase_price: 380000,
    },
    {
      id: "demo-prop-sonnenhang",
      organization_id: ORG,
      name: "Wohnpark Sonnenhang",
      property_type: "residential",
      street: "Sonnenweg 3",
      postal_code: "21029",
      city: "Hamburg",
      purchase_price: null,
    },
  ];

  const unit = (
    id: string,
    property_id: string,
    name: string,
    unit_type: string,
    status: string,
    area_sqm: number | null,
  ): Unit => ({ id, organization_id: ORG, property_id, name, unit_type, status, area_sqm });

  const units: Unit[] = [
    unit("demo-unit-l11", "demo-prop-lindenhof", "WE 1.1 EG links", "apartment", "occupied", 68.5),
    unit("demo-unit-l12", "demo-prop-lindenhof", "WE 1.2 EG rechts", "apartment", "occupied", 72),
    unit("demo-unit-l21", "demo-prop-lindenhof", "WE 2.1 OG links", "apartment", "vacant", 85),
    unit("demo-unit-l22", "demo-prop-lindenhof", "WE 2.2 OG rechts", "apartment", "reserved", 54),
    unit("demo-unit-k1", "demo-prop-kontorhaus", "Büro 1. OG", "commercial", "occupied", 210),
    unit("demo-unit-k2", "demo-prop-kontorhaus", "Ladenfläche EG", "commercial", "vacant", 140),
    unit("demo-unit-p01", "demo-prop-parkhaus", "Stellplatz 01", "garage", "occupied", 12.5),
    unit("demo-unit-p02", "demo-prop-parkhaus", "Stellplatz 02", "garage", "vacant", 12.5),
    unit("demo-unit-s1", "demo-prop-sonnenhang", "Haus A – WE 1", "apartment", "occupied", 95),
    unit("demo-unit-s2", "demo-prop-sonnenhang", "Haus A – WE 2", "apartment", "occupied", 78),
  ];

  const tenant = (
    id: string,
    first_name: string,
    last_name: string,
    email: string | null,
    phone: string | null,
    move_in_date: string | null,
    move_out_date: string | null = null,
  ): Tenant => ({
    id,
    organization_id: ORG,
    first_name,
    last_name,
    email,
    phone,
    move_in_date,
    move_out_date,
  });

  const tenants: Tenant[] = [
    tenant("demo-ten-schneider", "Anna", "Schneider", "anna.schneider@example.com", "+49 40 555 0111", month(-26, 1)),
    tenant("demo-ten-weber", "Jonas", "Weber", "jonas.weber@example.com", "+49 40 555 0112", month(-14, 1)),
    tenant("demo-ten-brandt", "Kanzlei", "Brandt & Partner", "empfang@brandt-partner.example", "+49 40 555 0113", month(-36, 1)),
    tenant("demo-ten-becker", "Lukas", "Becker", "lukas.becker@example.com", null, month(-8, 1)),
    tenant("demo-ten-wagner", "Sophie", "Wagner", "sophie.wagner@example.org", "+49 40 555 0115", month(-30, 15)),
    tenant("demo-ten-yilmaz", "Mehmet", "Yılmaz", "mehmet.yilmaz@example.org", "+49 40 555 0116", month(-20, 1)),
    tenant("demo-ten-hoffmann", "Clara", "Hoffmann", "clara.hoffmann@example.com", null, month(-40, 1), month(-2, 0)),
    tenant("demo-ten-fischer", "Leonie", "Fischer", "leonie.fischer@example.com", "+49 40 555 0118", month(1, 1)),
  ];

  const contract = (
    id: string,
    unit_id: string,
    tenant_id: string,
    start_date: string,
    end_date: string | null,
    cold_rent: number,
    service_charge_advance: number,
  ): Contract => ({
    id,
    organization_id: ORG,
    unit_id,
    tenant_id,
    start_date,
    end_date,
    cold_rent,
    service_charge_advance,
  });

  const contracts: Contract[] = [
    contract("demo-con-schneider", "demo-unit-l11", "demo-ten-schneider", month(-26, 1), null, 780, 190),
    contract("demo-con-weber", "demo-unit-l12", "demo-ten-weber", month(-14, 1), null, 820, 200),
    contract("demo-con-brandt", "demo-unit-k1", "demo-ten-brandt", month(-36, 1), month(24, 0), 2450, 520),
    contract("demo-con-becker", "demo-unit-p01", "demo-ten-becker", month(-8, 1), null, 95, 0),
    contract("demo-con-wagner", "demo-unit-s1", "demo-ten-wagner", month(-30, 15), null, 1150, 260),
    contract("demo-con-yilmaz", "demo-unit-s2", "demo-ten-yilmaz", month(-20, 1), null, 940, 220),
    contract("demo-con-hoffmann", "demo-unit-l21", "demo-ten-hoffmann", month(-40, 1), month(-2, 0), 900, 210),
    contract("demo-con-fischer", "demo-unit-l22", "demo-ten-fischer", month(1, 1), null, 640, 160),
  ];

  const vendors: Vendor[] = [
    {
      id: "demo-ven-haustechnik",
      organization_id: ORG,
      name: "Haustechnik Nord GmbH",
      service_type: "maintenance",
      contact_email: "service@haustechnik-nord.example",
      contact_phone: "+49 40 555 0201",
      notes: "Heizung & Sanitär, 24h-Notdienst (fiktiv).",
    },
    {
      id: "demo-ven-elektro",
      organization_id: ORG,
      name: "Elektro Blitz KG",
      service_type: "inspection",
      contact_email: "auftrag@elektro-blitz.example",
      contact_phone: "+49 40 555 0202",
      notes: "Rauchmelder- und E-Check-Wartung.",
    },
    {
      id: "demo-ven-gruen",
      organization_id: ORG,
      name: "Grünpflege Meier",
      service_type: "maintenance",
      contact_email: "info@gruenpflege-meier.example",
      contact_phone: null,
      notes: null,
    },
    {
      id: "demo-ven-glanz",
      organization_id: ORG,
      name: "Reinigungsservice Glanz",
      service_type: "cleaning",
      contact_email: "dispo@glanz-reinigung.example",
      contact_phone: "+49 40 555 0204",
      notes: "Treppenhausreinigung wöchentlich.",
    },
    {
      id: "demo-ven-dach",
      organization_id: ORG,
      name: "Dachdecker Hansen",
      service_type: "repair",
      contact_email: null,
      contact_phone: "+49 40 555 0205",
      notes: "Termine nur nach telefonischer Absprache.",
    },
  ];

  const invoice = (
    id: string,
    property_id: string | null,
    vendor_name: string,
    invoice_number: string,
    invoice_date: string,
    gross_amount: number,
    status: string,
  ): Invoice => ({
    id,
    organization_id: ORG,
    property_id,
    vendor_name,
    invoice_number,
    invoice_date,
    gross_amount,
    status,
  });

  const invoices: Invoice[] = [
    invoice("demo-inv-0141", "demo-prop-lindenhof", "Haustechnik Nord GmbH", `RE-${year}-0141`, day(-40), 1428, "paid"),
    invoice("demo-inv-0883", "demo-prop-sonnenhang", "Grünpflege Meier", "GM-0883", day(-25), 595, "paid"),
    invoice("demo-inv-77812", "demo-prop-lindenhof", "Hansewerk Energie (Demo)", "HE-77812", day(-18), 1240, "approved"),
    invoice("demo-inv-2211", "demo-prop-kontorhaus", "Reinigungsservice Glanz", "RG-2211", day(-12), 476, "approved"),
    invoice("demo-inv-5521", "demo-prop-lindenhof", "Elektro Blitz KG", "EB-5521", day(-6), 312.4, "received"),
    invoice("demo-inv-1902", "demo-prop-sonnenhang", "Dachdecker Hansen", "DH-1902", day(-3), 3867.5, "received"),
  ];

  const activeRentContracts = contracts.filter((item) =>
    ["demo-con-schneider", "demo-con-weber", "demo-con-brandt", "demo-con-becker", "demo-con-wagner", "demo-con-yilmaz"].includes(item.id),
  );
  const tenantById = new Map(tenants.map((item) => [item.id, item]));
  const unitById = new Map(units.map((item) => [item.id, item]));
  const monthLabel = (offset: number) =>
    new Date(`${month(offset, 1)}T00:00:00Z`).toLocaleDateString("de-DE", {
      month: "long",
      year: "numeric",
      timeZone: "UTC",
    });

  const payments: Payment[] = [];
  const bankTransactions: BankTransaction[] = [];
  const accountingEntries: AccountingEntry[] = [];

  for (const offset of [-2, -1]) {
    for (const item of activeRentContracts) {
      const rentTenant = tenantById.get(item.tenant_id);
      const rentUnit = unitById.get(item.unit_id);
      const amount = item.cold_rent + item.service_charge_advance;
      const paymentId = `demo-pay-${item.id.replace("demo-con-", "")}-m${Math.abs(offset)}`;
      const reference = `Miete ${monthLabel(offset)} ${rentUnit?.name ?? ""}`.trim();
      const bookingDate = month(offset, 3);
      payments.push({
        id: paymentId,
        organization_id: ORG,
        invoice_id: null,
        contract_id: item.id,
        amount,
        booking_date: bookingDate,
        reference,
      });
      // Die letzte Miete von Herrn Yılmaz ist bewusst noch nicht zugeordnet (Matching testbar).
      const unmatched = offset === -1 && item.id === "demo-con-yilmaz";
      bankTransactions.push({
        id: `demo-bank-${paymentId.replace("demo-pay-", "")}`,
        organization_id: ORG,
        payment_id: unmatched ? null : paymentId,
        external_id: `DEMO-${bookingDate.replace(/-/g, "")}-${item.id.slice(9, 13).toUpperCase()}`,
        account_name: "Mietkonto (Demo)",
        transaction_type: "credit",
        booking_date: bookingDate,
        value_date: bookingDate,
        amount,
        currency: "EUR",
        counterparty_name: rentTenant ? `${rentTenant.first_name} ${rentTenant.last_name}` : null,
        iban: "DE00 0000 0000 0000 0000 00",
        reference,
        status: unmatched ? "imported" : "matched",
      });
    }
  }

  const invoicePayments: Payment[] = [
    {
      id: "demo-pay-inv-0141",
      organization_id: ORG,
      invoice_id: "demo-inv-0141",
      contract_id: null,
      amount: 1428,
      booking_date: day(-30),
      reference: `RE-${year}-0141 Haustechnik Nord`,
    },
    {
      id: "demo-pay-inv-0883",
      organization_id: ORG,
      invoice_id: "demo-inv-0883",
      contract_id: null,
      amount: 595,
      booking_date: day(-15),
      reference: "GM-0883 Grünpflege",
    },
  ];
  payments.push(...invoicePayments);

  bankTransactions.push(
    {
      id: "demo-bank-inv-0141",
      organization_id: ORG,
      payment_id: "demo-pay-inv-0141",
      external_id: "DEMO-OUT-0141",
      account_name: "Geschäftskonto (Demo)",
      transaction_type: "debit",
      booking_date: day(-30),
      value_date: day(-30),
      amount: 1428,
      currency: "EUR",
      counterparty_name: "Haustechnik Nord GmbH",
      iban: "DE00 0000 0000 0000 0000 01",
      reference: `RE-${year}-0141`,
      status: "matched",
    },
    {
      id: "demo-bank-inv-0883",
      organization_id: ORG,
      payment_id: "demo-pay-inv-0883",
      external_id: "DEMO-OUT-0883",
      account_name: "Geschäftskonto (Demo)",
      transaction_type: "debit",
      booking_date: day(-15),
      value_date: day(-15),
      amount: 595,
      currency: "EUR",
      counterparty_name: "Grünpflege Meier",
      iban: "DE00 0000 0000 0000 0000 02",
      reference: "GM-0883",
      status: "matched",
    },
    {
      id: "demo-bank-energie",
      organization_id: ORG,
      payment_id: null,
      external_id: "DEMO-OUT-ENERGIE",
      account_name: "Geschäftskonto (Demo)",
      transaction_type: "debit",
      booking_date: day(-4),
      value_date: day(-4),
      amount: 420,
      currency: "EUR",
      counterparty_name: "Hansewerk Energie (Demo)",
      iban: "DE00 0000 0000 0000 0000 03",
      reference: "Abschlag Allgemeinstrom",
      status: "imported",
    },
  );
  bankTransactions.sort((left, right) => (right.booking_date ?? "").localeCompare(left.booking_date ?? ""));
  payments.sort((left, right) => (right.booking_date ?? "").localeCompare(left.booking_date ?? ""));

  // Mieteinnahmen je Immobilie und Monat als Accounting-Einträge (Summen passen zu den Zahlungen).
  for (const offset of [-2, -1]) {
    for (const property of properties) {
      const total = activeRentContracts
        .filter((item) => unitById.get(item.unit_id)?.property_id === property.id)
        .reduce((sum, item) => sum + item.cold_rent + item.service_charge_advance, 0);
      if (total > 0) {
        accountingEntries.push({
          id: `demo-acc-rent-${property.id.replace("demo-prop-", "")}-m${Math.abs(offset)}`,
          organization_id: ORG,
          property_id: property.id,
          entry_type: "income",
          category: "rent",
          amount: total,
          booking_date: month(offset, 3),
        });
      }
    }
  }
  accountingEntries.push(
    {
      id: "demo-acc-exp-0141",
      organization_id: ORG,
      property_id: "demo-prop-lindenhof",
      entry_type: "expense",
      category: "maintenance",
      amount: 1428,
      booking_date: day(-30),
    },
    {
      id: "demo-acc-exp-0883",
      organization_id: ORG,
      property_id: "demo-prop-sonnenhang",
      entry_type: "expense",
      category: "gardening",
      amount: 595,
      booking_date: day(-15),
    },
    {
      id: "demo-acc-exp-insurance",
      organization_id: ORG,
      property_id: "demo-prop-kontorhaus",
      entry_type: "expense",
      category: "insurance",
      amount: 2140,
      booking_date: month(-1, 15),
    },
    {
      id: "demo-acc-exp-tax",
      organization_id: ORG,
      property_id: null,
      entry_type: "expense",
      category: "property_tax",
      amount: 860.75,
      booking_date: month(-2, 15),
    },
  );
  accountingEntries.sort((left, right) => (right.booking_date ?? "").localeCompare(left.booking_date ?? ""));

  const operatingCostPeriods: OperatingCostPeriod[] = [
    {
      id: "demo-ocp-lindenhof-current",
      organization_id: ORG,
      property_id: "demo-prop-lindenhof",
      name: `Betriebskosten ${year} Lindenhof`,
      period_start: `${year}-01-01`,
      period_end: `${year}-12-31`,
      status: "draft",
    },
    {
      id: "demo-ocp-lindenhof-previous",
      organization_id: ORG,
      property_id: "demo-prop-lindenhof",
      name: `Betriebskosten ${previousYear} Lindenhof`,
      period_start: `${previousYear}-01-01`,
      period_end: `${previousYear}-12-31`,
      status: "finalized",
    },
    {
      id: "demo-ocp-sonnenhang-previous",
      organization_id: ORG,
      property_id: "demo-prop-sonnenhang",
      name: `Betriebskosten ${previousYear} Sonnenhang`,
      period_start: `${previousYear}-01-01`,
      period_end: `${previousYear}-12-31`,
      status: "draft",
    },
  ];

  const costItem = (
    id: string,
    period_id: string,
    category: string,
    description: string | null,
    allocation_method: string,
    amount: number,
    billable = true,
  ): OperatingCostItem => ({
    id,
    organization_id: ORG,
    period_id,
    category,
    description,
    allocation_method,
    amount,
    billable,
  });

  const operatingCostItems: OperatingCostItem[] = [
    costItem("demo-oci-l-heat", "demo-ocp-lindenhof-previous", "heating", "Fernwärme inkl. Messdienst", "area", 6840),
    costItem("demo-oci-l-water", "demo-ocp-lindenhof-previous", "water", "Frisch- und Abwasser", "occupancy_days", 2150),
    costItem("demo-oci-l-waste", "demo-ocp-lindenhof-previous", "waste", "Müllabfuhr", "unit_count", 980),
    costItem("demo-oci-l-ins", "demo-ocp-lindenhof-previous", "insurance", "Gebäudeversicherung", "area", 1420),
    costItem("demo-oci-l-admin", "demo-ocp-lindenhof-previous", "administration", "Verwaltungskosten (nicht umlagefähig)", "unit_count", 900, false),
    costItem("demo-oci-lc-heat", "demo-ocp-lindenhof-current", "heating", "Abschlag Fernwärme bis heute", "area", 4980),
    costItem("demo-oci-lc-clean", "demo-ocp-lindenhof-current", "cleaning", "Treppenhausreinigung", "advance_share", 1320),
    costItem("demo-oci-s-heat", "demo-ocp-sonnenhang-previous", "heating", "Gasheizung", "area", 3920),
    costItem("demo-oci-s-garden", "demo-ocp-sonnenhang-previous", "gardening", "Gartenpflege", "unit_count", 1190),
  ];

  const tasks: TaskItem[] = [
    {
      id: "demo-task-heizung",
      organization_id: ORG,
      property_id: "demo-prop-lindenhof",
      unit_id: "demo-unit-l12",
      vendor_id: "demo-ven-haustechnik",
      recurring_template_id: null,
      title: "Heizung WE 1.2 fällt aus",
      description: "Mieter meldet kalte Heizkörper im Wohnzimmer.",
      category: "tenant_request",
      priority: "urgent",
      status: "in_progress",
      due_date: day(-2),
      estimated_cost: 450,
      actual_cost: null,
      assignee_name: "Haustechnik Nord – Hr. Petersen",
      completion_notes: null,
      completed_at: null,
      source: "manual",
    },
    {
      id: "demo-task-dachrinne",
      organization_id: ORG,
      property_id: "demo-prop-sonnenhang",
      unit_id: null,
      vendor_id: "demo-ven-dach",
      recurring_template_id: null,
      title: "Dachrinne Haus A reinigen und abdichten",
      description: "Wartet auf Freigabe des Angebots DH-1902.",
      category: "maintenance",
      priority: "medium",
      status: "blocked",
      due_date: day(-7),
      estimated_cost: 650,
      actual_cost: null,
      assignee_name: "Max Manager",
      completion_notes: null,
      completed_at: null,
      source: "manual",
    },
    {
      id: "demo-task-reinigung",
      organization_id: ORG,
      property_id: "demo-prop-kontorhaus",
      unit_id: null,
      vendor_id: "demo-ven-glanz",
      recurring_template_id: null,
      title: "Treppenhausreinigung kontrollieren",
      description: "Stichprobe nach Beschwerde aus dem Büro 1. OG.",
      category: "inspection",
      priority: "low",
      status: "open",
      due_date: day(5),
      estimated_cost: null,
      actual_cost: null,
      assignee_name: "Dana Demo",
      completion_notes: null,
      completed_at: null,
      source: "manual",
    },
    {
      id: "demo-task-nk-versand",
      organization_id: ORG,
      property_id: "demo-prop-lindenhof",
      unit_id: null,
      vendor_id: null,
      recurring_template_id: null,
      title: `Nebenkostenabrechnung ${previousYear} versenden`,
      description: "Finalisierte Abrechnung an alle Mieter des Lindenhofs schicken.",
      category: "accounting",
      priority: "high",
      status: "open",
      due_date: day(10),
      estimated_cost: null,
      actual_cost: null,
      assignee_name: "Dana Demo",
      completion_notes: null,
      completed_at: null,
      source: "manual",
    },
    {
      id: "demo-task-uebergabe",
      organization_id: ORG,
      property_id: "demo-prop-lindenhof",
      unit_id: "demo-unit-l22",
      vendor_id: null,
      recurring_template_id: null,
      title: "Wohnungsübergabe WE 2.2 an Leonie Fischer",
      description: "Übergabeprotokoll und Schlüssel vorbereiten.",
      category: "tenant_request",
      priority: "medium",
      status: "open",
      due_date: month(1, 1),
      estimated_cost: null,
      actual_cost: null,
      assignee_name: "Max Manager",
      completion_notes: null,
      completed_at: null,
      source: "manual",
    },
    {
      id: "demo-task-rauchmelder",
      organization_id: ORG,
      property_id: "demo-prop-lindenhof",
      unit_id: null,
      vendor_id: "demo-ven-elektro",
      recurring_template_id: "demo-tpl-rauchmelder",
      title: "Rauchmelderwartung Lindenhof",
      description: "Jährliche Prüfung aller Rauchmelder.",
      category: "compliance",
      priority: "high",
      status: "done",
      due_date: day(-20),
      estimated_cost: 380,
      actual_cost: 356,
      assignee_name: "Elektro Blitz KG",
      completion_notes: "Alle 14 Melder geprüft, 2 Batterien getauscht.",
      completed_at: timestamp(-21, 14, 30),
      source: "recurring",
    },
    {
      id: "demo-task-garten",
      organization_id: ORG,
      property_id: "demo-prop-sonnenhang",
      unit_id: null,
      vendor_id: "demo-ven-gruen",
      recurring_template_id: null,
      title: "Gartenpflege Herbstschnitt",
      description: null,
      category: "maintenance",
      priority: "low",
      status: "done",
      due_date: day(-27),
      estimated_cost: 600,
      actual_cost: 595,
      assignee_name: "Grünpflege Meier",
      completion_notes: "Abgerechnet mit Rechnung GM-0883.",
      completed_at: timestamp(-26, 16),
      source: "manual",
    },
    {
      id: "demo-task-garagentor",
      organization_id: ORG,
      property_id: "demo-prop-parkhaus",
      unit_id: "demo-unit-p01",
      vendor_id: null,
      recurring_template_id: null,
      title: "Garagentor klemmt",
      description: "Hat sich nach Schmierung erledigt.",
      category: "other",
      priority: "medium",
      status: "cancelled",
      due_date: day(-30),
      estimated_cost: 120,
      actual_cost: null,
      assignee_name: null,
      completion_notes: null,
      completed_at: null,
      source: "manual",
    },
  ];

  const taskTemplates: TaskTemplate[] = [
    {
      id: "demo-tpl-begehung",
      organization_id: ORG,
      property_id: "demo-prop-kontorhaus",
      unit_id: null,
      vendor_id: null,
      title: "Monatliche Objektbegehung Kontorhaus",
      description: "Sichtprüfung Fluchtwege, Beleuchtung und Außenanlagen.",
      category: "inspection",
      priority: "medium",
      recurrence_frequency: "monthly",
      next_due_date: day(-1),
      assignee_name: "Max Manager",
      active: true,
    },
    {
      id: "demo-tpl-rauchmelder",
      organization_id: ORG,
      property_id: "demo-prop-lindenhof",
      unit_id: null,
      vendor_id: "demo-ven-elektro",
      title: "Rauchmelderwartung Lindenhof",
      description: "Jährliche Prüfung aller Rauchmelder.",
      category: "compliance",
      priority: "high",
      recurrence_frequency: "yearly",
      next_due_date: day(345),
      assignee_name: "Elektro Blitz KG",
      active: true,
    },
    {
      id: "demo-tpl-heizung",
      organization_id: ORG,
      property_id: "demo-prop-sonnenhang",
      unit_id: null,
      vendor_id: "demo-ven-haustechnik",
      title: "Heizungswartung Sonnenhang",
      description: "Pausiert bis zum Austausch der Gastherme.",
      category: "maintenance",
      priority: "low",
      recurrence_frequency: "quarterly",
      next_due_date: day(30),
      assignee_name: null,
      active: false,
    },
  ];

  const taskComments: TaskComment[] = [
    {
      id: "demo-comment-1",
      organization_id: ORG,
      task_id: "demo-task-heizung",
      author_user_id: DEMO_OWNER_ID,
      author_email: "demo@propertyhub.example",
      message: "Mieter informiert, Techniker kommt morgen Vormittag.",
      created_at: timestamp(-3, 10, 15),
    },
    {
      id: "demo-comment-2",
      organization_id: ORG,
      task_id: "demo-task-heizung",
      author_user_id: "demo-user-manager",
      author_email: "manager@propertyhub.example",
      message: "Ersatzteil (Thermostatkopf) ist bestellt.",
      created_at: timestamp(-1, 16, 40),
    },
    {
      id: "demo-comment-3",
      organization_id: ORG,
      task_id: "demo-task-dachrinne",
      author_user_id: "demo-user-manager",
      author_email: "manager@propertyhub.example",
      message: "Angebot liegt vor, Freigabe durch Eigentümer ausstehend.",
      created_at: timestamp(-5, 11),
    },
  ];

  const document = (
    id: string,
    related_model: string,
    related_id: string,
    document_type: string,
    file_name: string,
    createdOffset: number,
    ocr: Partial<DocumentRecord> = {},
  ): DocumentRecord => ({
    id,
    organization_id: ORG,
    created_at: timestamp(createdOffset, 8, 30),
    related_model,
    related_id,
    document_type,
    file_name,
    storage_path: null,
    ocr_status: "pending",
    ocr_error: null,
    ocr_attempt_count: 0,
    ocr_started_at: null,
    ocr_result: null,
    ocr_processed_at: null,
    ...ocr,
  });

  const documents: DocumentRecord[] = [
    document("demo-doc-1902", "invoice", "demo-inv-1902", "invoice_receipt", "dachdecker-hansen-scan-unscharf.png", -3, {
      ocr_status: "failed",
      ocr_error: "Text konnte nicht zuverlässig erkannt werden (Demo-Simulation).",
      ocr_attempt_count: 1,
      ocr_started_at: timestamp(-3, 8, 31),
    }),
    document("demo-doc-heizung", "task", "demo-task-heizung", "task_attachment", "heizung-fehlerbild.jpg", -2),
    document("demo-doc-5521", "invoice", "demo-inv-5521", "invoice_receipt", "elektro-blitz-eb-5521.pdf", -6),
    document("demo-doc-2211", "invoice", "demo-inv-2211", "invoice_receipt", "glanz-rg-2211.pdf", -12, {
      ocr_status: "processed",
      ocr_attempt_count: 1,
      ocr_started_at: timestamp(-12, 8, 31),
      ocr_processed_at: timestamp(-12, 8, 32),
      ocr_result: {
        vendor_name: "Reinigungsservice Glanz",
        invoice_number: "RG-2211",
        invoice_date: day(-12),
        gross_amount: 476,
        confidence: 1,
        source: "pdf_text",
        status: "processed",
      },
    }),
    document("demo-doc-energieausweis", "property", "demo-prop-lindenhof", "property_document", "energieausweis-lindenhof.pdf", -60),
    document("demo-doc-0141", "invoice", "demo-inv-0141", "invoice_receipt", `haustechnik-nord-re-${year}-0141.pdf`, -40, {
      ocr_status: "processed",
      ocr_attempt_count: 1,
      ocr_started_at: timestamp(-40, 8, 31),
      ocr_processed_at: timestamp(-40, 8, 32),
      ocr_result: {
        vendor_name: "Haustechnik Nord GmbH",
        invoice_number: `RE-${year}-0141`,
        invoice_date: day(-40),
        gross_amount: 1428,
        confidence: 1,
        source: "pdf_text",
        status: "processed",
      },
    }),
  ];

  const audit = (
    id: string,
    offset: number,
    actor: "owner" | "manager",
    action: string,
    resource_type: string,
    resource_id: string | null,
    summary: string,
    details: AuditLogEntry["details"] = null,
  ): AuditLogEntry => ({
    id,
    organization_id: ORG,
    actor_user_id: actor === "owner" ? DEMO_OWNER_ID : "demo-user-manager",
    actor_email: actor === "owner" ? "demo@propertyhub.example" : "manager@propertyhub.example",
    action,
    resource_type,
    resource_id,
    summary,
    details,
    created_at: timestamp(offset, 9 + (Math.abs(offset) % 8), 5),
  });

  const auditLogs: AuditLogEntry[] = [
    audit("demo-audit-01", -1, "manager", "task.updated", "task", "demo-task-heizung", "Aufgabe Heizung WE 1.2 fällt aus aktualisiert", { status: "in_progress" }),
    audit("demo-audit-02", -2, "owner", "user.invited", "user", "demo-user-invited", "Einladung für neu@propertyhub.example erstellt", { role: "manager" }),
    audit("demo-audit-03", -3, "manager", "document.uploaded", "document", "demo-doc-1902", "Dokument dachdecker-hansen-scan-unscharf.png hochgeladen"),
    audit("demo-audit-04", -3, "manager", "invoice.created", "invoice", "demo-inv-1902", "Rechnung DH-1902 angelegt"),
    audit("demo-audit-05", -4, "owner", "task.created", "task", "demo-task-heizung", "Aufgabe Heizung WE 1.2 fällt aus angelegt"),
    audit("demo-audit-06", -6, "manager", "invoice.created", "invoice", "demo-inv-5521", "Rechnung EB-5521 angelegt"),
    audit("demo-audit-07", -8, "owner", "bank_transaction.imported", "bank_transaction", null, "Bankdatei kontoauszug-demo.csv importiert", { imported_count: 14 }),
    audit("demo-audit-08", -12, "manager", "document.ocr_applied", "document", "demo-doc-2211", "OCR-Daten aus Dokument glanz-rg-2211.pdf auf Rechnung angewendet"),
    audit("demo-audit-09", -15, "owner", "payment.created", "payment", "demo-pay-inv-0883", "Zahlung demo-pay-inv-0883 angelegt"),
    audit("demo-audit-10", -21, "manager", "task.updated", "task", "demo-task-rauchmelder", "Aufgabe Rauchmelderwartung Lindenhof aktualisiert", { status: "done" }),
    audit("demo-audit-11", -30, "owner", "operating_cost_period.finalized", "operating_cost_period", "demo-ocp-lindenhof-previous", `Nebenkostenperiode Betriebskosten ${previousYear} Lindenhof finalisiert`),
    audit("demo-audit-12", -45, "owner", "contract.created", "contract", "demo-con-fischer", "Vertrag demo-con-fischer angelegt"),
    audit("demo-audit-13", -46, "owner", "tenant.created", "tenant", "demo-ten-fischer", "Mieter Leonie Fischer angelegt"),
    audit("demo-audit-14", -60, "owner", "organization.updated", "organization", ORG, "Organisation Musterverwaltung Nord (Demo) aktualisiert"),
    audit("demo-audit-15", -61, "manager", "vendor.created", "vendor", "demo-ven-dach", "Dienstleister Dachdecker Hansen angelegt"),
  ];

  return {
    version: DEMO_DATA_VERSION,
    seeded_at: now.toISOString(),
    sequence: 1,
    organization,
    users,
    properties,
    units,
    tenants,
    contracts,
    invoices,
    payments,
    bank_transactions: bankTransactions,
    accounting_entries: accountingEntries,
    operating_cost_periods: operatingCostPeriods,
    operating_cost_items: operatingCostItems,
    vendors,
    tasks,
    task_comments: taskComments,
    task_templates: taskTemplates,
    documents,
    audit_logs: auditLogs,
    ocr_jobs: {},
  };
}
