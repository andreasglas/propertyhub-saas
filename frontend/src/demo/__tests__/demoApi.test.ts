import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.hoisted(() => {
  // Muss vor dem Import des apiClient gesetzt sein (Flag wird beim Laden ausgewertet).
  (import.meta.env as Record<string, string>).VITE_DEMO_MODE = "true";
});

import { listAccountingEntries, createAccountingEntry } from "../../services/accountingService";
import { apiClient, setAuthToken } from "../../services/apiClient";
import { listAuditLogs } from "../../services/auditLogService";
import { getCurrentUser, getInvitationInfo, login, setupPassword } from "../../services/authService";
import {
  importBankTransactions,
  listBankTransactions,
  matchBankTransaction,
} from "../../services/bankingService";
import { createContract, listContracts } from "../../services/contractService";
import {
  applyDocumentOcrToInvoice,
  listDocuments,
  processDocumentOcr,
  retryDocumentOcr,
  uploadDocument,
} from "../../services/documentService";
import { createInvoice, listInvoices } from "../../services/invoiceService";
import {
  createOperatingCostItem,
  createOperatingCostPeriod,
  downloadOperatingCostSettlementCsv,
  downloadOperatingCostSettlementPdf,
  finalizeOperatingCostPeriod,
  getOperatingCostSettlementPreview,
  listOperatingCostItems,
  listOperatingCostPeriods,
} from "../../services/operatingCostService";
import { getCurrentOrganization, updateCurrentOrganization } from "../../services/organizationService";
import { createPayment, listPayments } from "../../services/paymentService";
import { createProperty, listProperties } from "../../services/propertyService";
import { downloadTaskReportCsv, getDashboardReport } from "../../services/reportService";
import {
  createTask,
  createTaskComment,
  createTaskTemplate,
  deleteTask,
  generateDueTasks,
  listTaskAttachments,
  listTaskComments,
  listTaskHistory,
  listTasks,
  listTaskTemplates,
  updateTask,
} from "../../services/taskService";
import { createTenant, listTenants } from "../../services/tenantService";
import { createUnit, listUnits } from "../../services/unitService";
import {
  createUser,
  inviteUser,
  listUsers,
  resendUserInvitation,
  updateUser,
} from "../../services/userAdminService";
import { createVendor, listVendors } from "../../services/vendorService";
import { DEMO_ACCOUNTS, DEMO_PASSWORD, DEMO_STORAGE_KEYS } from "../demoConfig";
import { DEMO_OCR_TIMINGS, DEMO_UNSUPPORTED_MESSAGE, handleDemoRequest } from "../demoApi";
import { resetDemoStore } from "../demoStore";
import { blockNetwork } from "./networkGuard";

let networkAttempts: string[] = [];

async function signIn(email: string = DEMO_ACCOUNTS[0].email) {
  const token = await login(email, DEMO_PASSWORD);
  setAuthToken(token.access_token);
  return token.access_token;
}

function statusOf(error: unknown) {
  return (error as { response?: { status?: number } }).response?.status;
}

async function expectStatus(promise: Promise<unknown>, status: number) {
  const error = await promise.then(
    () => null,
    (caught: unknown) => caught,
  );
  expect(error, `Erwarteter HTTP-Status ${status}`).not.toBeNull();
  expect(statusOf(error)).toBe(status);
  return error;
}

function readBlob(blob: Blob) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsText(blob);
  });
}

function round2(value: number) {
  return Math.round(value * 100) / 100;
}

beforeEach(() => {
  window.localStorage.clear();
  resetDemoStore();
  networkAttempts = blockNetwork();
});

afterEach(() => {
  // Kernzusage: Im Demo-Modus wird niemals ein Backend-Request ausgelöst.
  expect(networkAttempts).toEqual([]);
  setAuthToken(null);
  vi.unstubAllGlobals();
});

describe("Demo-API: Authentifizierung und Rollen", () => {
  it("verlangt eine gültige Demo-Sitzung", async () => {
    await expectStatus(listProperties(), 401);
    setAuthToken("demo.erfunden.0123456789abcdef0123456789abcdef");
    await expectStatus(listProperties(), 401);
  });

  it("liefert für jedes Demo-Konto die passende Rolle", async () => {
    for (const account of DEMO_ACCOUNTS) {
      await signIn(account.email);
      const user = await getCurrentUser();
      expect(user.email).toBe(account.email);
      expect(user.role).toBe(account.role);
    }
  });

  it("erlaubt Viewern nur lesenden Zugriff und Managern keine Benutzerverwaltung", async () => {
    await signIn("viewer@propertyhub.example");
    expect((await listProperties()).length).toBeGreaterThan(0);
    await expectStatus(
      createProperty({ name: "Viewer-Test", property_type: "residential" }),
      403,
    );
    await expectStatus(listUsers(), 403);

    await signIn("manager@propertyhub.example");
    expect((await listUsers()).length).toBeGreaterThan(0);
    await expectStatus(inviteUser({ email: "neu@example.com", role: "viewer" }), 403);
  });

  it("beantwortet nicht unterstützte Operationen verständlich mit 501 statt Netzwerkzugriff", async () => {
    await signIn();
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    const error = await expectStatus(apiClient.delete("/properties/demo-prop-hafen"), 501);
    expect((error as { response: { data: { detail: string } } }).response.data.detail).toBe(
      DEMO_UNSUPPORTED_MESSAGE,
    );
    expect(warn).toHaveBeenCalled();
  });
});

describe("Demo-API: konsistente Beispieldaten", () => {
  it("liefert verknüpfte Stammdaten, Status-Varianten und stimmige Summen", async () => {
    await signIn();
    const [properties, units, tenants, contracts, invoices, payments, accounting, bank, tasks, vendors, documents] =
      await Promise.all([
        listProperties(),
        listUnits(),
        listTenants(),
        listContracts(),
        listInvoices(),
        listPayments(),
        listAccountingEntries(),
        listBankTransactions(),
        listTasks(),
        listVendors(),
        listDocuments(),
      ]);

    const propertyIds = new Set(properties.map((item) => item.id));
    const unitIds = new Set(units.map((item) => item.id));
    const tenantIds = new Set(tenants.map((item) => item.id));
    const contractIds = new Set(contracts.map((item) => item.id));
    const invoiceIds = new Set(invoices.map((item) => item.id));
    const paymentIds = new Set(payments.map((item) => item.id));

    expect(units.every((unit) => propertyIds.has(unit.property_id))).toBe(true);
    expect(contracts.every((contract) => unitIds.has(contract.unit_id) && tenantIds.has(contract.tenant_id))).toBe(true);
    expect(
      payments.every(
        (payment) =>
          (payment.invoice_id ? invoiceIds.has(payment.invoice_id) : true) &&
          (payment.contract_id ? contractIds.has(payment.contract_id) : true) &&
          Boolean(payment.invoice_id || payment.contract_id),
      ),
    ).toBe(true);
    expect(bank.every((transaction) => !transaction.payment_id || paymentIds.has(transaction.payment_id))).toBe(true);
    expect(tasks.every((task) => !task.property_id || propertyIds.has(task.property_id))).toBe(true);
    expect(tasks.every((task) => !task.vendor_id || vendors.some((vendor) => vendor.id === task.vendor_id))).toBe(true);

    expect(new Set(units.map((unit) => unit.status)).size).toBeGreaterThanOrEqual(2);
    expect(new Set(invoices.map((invoice) => invoice.status)).size).toBeGreaterThanOrEqual(3);
    expect(new Set(bank.map((transaction) => transaction.status))).toEqual(new Set(["matched", "imported"]));
    expect(new Set(tasks.map((task) => task.status)).size).toBeGreaterThanOrEqual(3);
    expect(new Set(documents.map((document) => document.ocr_status)).size).toBeGreaterThanOrEqual(3);

    const report = await getDashboardReport();
    expect(report.properties_count).toBe(properties.length);
    expect(report.units_count).toBe(units.length);
    expect(report.tenants_count).toBe(tenants.length);
    expect(report.contracts_count).toBe(contracts.length);
    expect(report.invoices_count).toBe(invoices.length);
    expect(report.payments_count).toBe(payments.length);
    expect(report.accounting_entries_count).toBe(accounting.length);
    expect(report.total_payment_amount).toBeCloseTo(
      round2(payments.reduce((sum, payment) => sum + payment.amount, 0)),
      2,
    );
    expect(report.total_invoice_amount).toBeCloseTo(
      round2(invoices.reduce((sum, invoice) => sum + invoice.gross_amount, 0)),
      2,
    );
    expect(report.overdue_tasks_count).toBeGreaterThan(0);
  });

  it("liefert Organisation, Benutzer, Audit-Log und Exporte", async () => {
    await signIn();
    const organization = await getCurrentOrganization();
    expect(organization.name).toContain("Demo");
    const users = await listUsers();
    expect(users.some((user) => !user.is_active)).toBe(true);
    expect(users.some((user) => user.invitation_sent_at && !user.invitation_accepted_at)).toBe(true);

    const logs = await listAuditLogs({ limit: 5 });
    expect(logs).toHaveLength(5);
    const filtered = await listAuditLogs({ resource_type: "task" });
    expect(filtered.length).toBeGreaterThan(0);
    expect(filtered.every((entry) => entry.resource_type === "task")).toBe(true);

    const csv = await readBlob(await downloadTaskReportCsv());
    expect(csv.split("\r\n")[0]).toContain("title");
    const periods = await listOperatingCostPeriods();
    const pdf = await readBlob(await downloadOperatingCostSettlementPdf(periods[0].id));
    expect(pdf.startsWith("%PDF-")).toBe(true);
    const settlementCsv = await readBlob(await downloadOperatingCostSettlementCsv(periods[0].id));
    expect(settlementCsv.length).toBeGreaterThan(0);
  });
});

describe("Demo-API: Formularaktionen und lokale Persistenz", () => {
  it("legt Stammdaten an, speichert sie versioniert im Browser und setzt sie zurück", async () => {
    await signIn();
    const property = await createProperty({
      name: "Testhaus Demo",
      property_type: "residential",
      street: "Teststraße 1",
      postal_code: "12345",
      city: "Teststadt",
    });
    const unit = await createUnit({ property_id: property.id, name: "WE 1", unit_type: "apartment", area_sqm: 50, status: "vacant" });
    const tenant = await createTenant({ first_name: "Test", last_name: "Mieter", email: "test@example.com" });
    const contract = await createContract({
      unit_id: unit.id,
      tenant_id: tenant.id,
      start_date: "2026-01-01",
      cold_rent: 500,
      service_charge_advance: 100,
    });
    await createPayment({ contract_id: contract.id, amount: 600, booking_date: "2026-01-03", reference: "Miete Januar" });
    const vendor = await createVendor({ name: "Testdienst", service_type: "Hausmeister" });
    await createInvoice({ vendor_name: vendor.name, invoice_number: "T-1", gross_amount: 119, status: "received", property_id: property.id });
    await createAccountingEntry({ booking_date: "2026-01-03", entry_type: "income", amount: 600, category: "rent", property_id: property.id });

    expect((await listProperties()).some((item) => item.id === property.id)).toBe(true);
    expect((await listContracts()).some((item) => item.id === contract.id)).toBe(true);
    expect(window.localStorage.getItem(DEMO_STORAGE_KEYS.data)).toContain("Testhaus Demo");
    expect(window.localStorage.getItem("propertyhub.auth.token")).toBeNull();

    await expectStatus(
      createContract({ unit_id: "gibt-es-nicht", tenant_id: tenant.id, start_date: "2026-01-01", cold_rent: 1, service_charge_advance: 0 }),
      404,
    );
    await expectStatus(createPayment({ amount: 1, booking_date: "2026-01-01" }), 422);

    resetDemoStore();
    expect((await listProperties()).some((item) => item.id === property.id)).toBe(false);
  });

  it("bearbeitet, kommentiert und löscht Aufgaben inklusive Historie und Audit-Log", async () => {
    await signIn();
    const created = await createTask({ title: "Demo-Testaufgabe", status: "open", priority: "high", category: "maintenance", source: "manual" });
    const updated = await updateTask(created.id, { ...created, status: "done", actual_cost: 250 });
    expect(updated.status).toBe("done");
    await createTaskComment(created.id, "Erledigt im Test");
    expect((await listTaskComments(created.id)).map((comment) => comment.message)).toContain("Erledigt im Test");
    expect((await listTaskHistory(created.id)).length).toBeGreaterThan(0);
    expect(Array.isArray(await listTaskAttachments(created.id))).toBe(true);

    await deleteTask(created.id);
    expect((await listTasks()).some((task) => task.id === created.id)).toBe(false);
    const logs = await listAuditLogs({ resource_type: "task" });
    expect(logs.some((entry) => entry.action === "task.deleted")).toBe(true);

    const templatesBefore = await listTaskTemplates();
    await createTaskTemplate({ title: "Monatliche Prüfung", recurrence_frequency: "monthly", next_due_date: "2020-01-01", active: true, priority: "medium", category: "inspection" });
    expect((await listTaskTemplates()).length).toBe(templatesBefore.length + 1);
    const generated = await generateDueTasks();
    expect(generated.generated_count).toBeGreaterThan(0);
    expect(generated.tasks.some((task) => task.title === "Monatliche Prüfung")).toBe(true);
  });

  it("simuliert Bankimport und Zahlungsabgleich", async () => {
    await signIn();
    const imported = await importBankTransactions();
    expect(imported.imported_count).toBeGreaterThan(0);
    const open = (await listBankTransactions()).find((transaction) => transaction.status === "imported");
    expect(open).toBeDefined();
    const payment = (await listPayments())[0];
    const matched = await matchBankTransaction(open!.id, payment.id);
    expect(matched.status).toBe("matched");
    expect(matched.payment_id).toBe(payment.id);
  });

  it("berechnet Betriebskostenabrechnungen mit stimmigen Summen", async () => {
    await signIn();
    const periods = await listOperatingCostPeriods();
    expect(periods.length).toBeGreaterThan(0);
    for (const period of periods) {
      const preview = await getOperatingCostSettlementPreview(period.id);
      const items = await listOperatingCostItems(period.id);
      const billable = round2(items.filter((item) => item.billable).reduce((sum, item) => sum + item.amount, 0));
      expect(preview.total_billable_amount).toBeCloseTo(billable, 2);
      const shares = round2(preview.lines.reduce((sum, line) => sum + line.share_amount, 0));
      expect(shares).toBeCloseTo(preview.total_billable_amount, 2);
      for (const line of preview.lines) {
        expect(line.balance_amount).toBeCloseTo(round2(line.share_amount - line.advance_paid_amount), 2);
      }
    }

    const property = (await listProperties())[0];
    const period = await createOperatingCostPeriod({ property_id: property.id, name: "Testperiode", period_start: "2025-01-01", period_end: "2025-12-31", status: "draft" });
    await createOperatingCostItem(period.id, { category: "Grundsteuer", amount: 1200, allocation_method: "area", billable: true });
    const preview = await getOperatingCostSettlementPreview(period.id);
    expect(preview.total_billable_amount).toBe(1200);
    const finalized = await finalizeOperatingCostPeriod(period.id);
    expect(finalized.status).not.toBe(period.status);
  });

  it("simuliert Upload und OCR ohne externe Dienste", async () => {
    await signIn();
    const invoice = (await listInvoices())[0];
    const file = new File(["Rechnung"], "rechnung-unscharf.pdf", { type: "application/pdf" });
    const document = await uploadDocument({ related_model: "invoice", related_id: invoice.id, document_type: "invoice", file });
    expect(document.ocr_status).toBe("pending");
    expect(document.storage_path ?? null).toBeNull();

    const queued = await processDocumentOcr(document.id);
    expect(queued.ocr_status).toBe("queued");

    const authorization = "Bearer " + (await signIn());
    const later = (offsetMs: number) => new Date(Date.now() + offsetMs);
    const readDocument = (offsetMs: number) => {
      const reply = handleDemoRequest({ method: "get", url: "/documents/", authorization }, later(offsetMs));
      return (reply.data as Array<{ id: string; ocr_status: string }>).find((item) => item.id === document.id);
    };
    expect(readDocument(DEMO_OCR_TIMINGS.processingAfterMs + 100)?.ocr_status).toBe("processing");
    expect(readDocument(DEMO_OCR_TIMINGS.finishedAfterMs + 100)?.ocr_status).toBe("failed");

    const retried = await retryDocumentOcr(document.id);
    expect(retried.ocr_status).toBe("queued");
    expect(readDocument(2 * DEMO_OCR_TIMINGS.finishedAfterMs + 1000)?.ocr_status).toBe("processed");

    const applied = await applyDocumentOcrToInvoice(document.id);
    expect(applied.invoice.id).toBe(invoice.id);
  });

  it("verwaltet Organisation, Benutzer und Einladungen lokal", async () => {
    await signIn();
    const organization = await updateCurrentOrganization({ name: "Demo Hausverwaltung Test", country: "DE" });
    expect(organization.name).toBe("Demo Hausverwaltung Test");

    const created = await createUser({ email: "neu.anlage@example.com", full_name: "Neu Anlage", password: "irrelevant-1", role: "viewer", is_active: true });
    expect(window.localStorage.getItem(DEMO_STORAGE_KEYS.data)).not.toContain("irrelevant-1");
    const updated = await updateUser(created.id, { role: "viewer", is_active: false });
    expect(updated.is_active).toBe(false);

    const invitation = await inviteUser({ email: "eingeladen@example.com", full_name: "Eingeladen", role: "manager" });
    expect(invitation.setup_path).toContain("setup-password?token=");
    const token = new URL(invitation.setup_path, "https://demo.invalid").searchParams.get("token")!;
    const resent = await resendUserInvitation(invitation.user.id);
    expect(resent.setup_path).not.toBe(invitation.setup_path);

    const resentToken = new URL(resent.setup_path, "https://demo.invalid").searchParams.get("token")!;
    await expectStatus(getInvitationInfo(token), 404);
    const info = await getInvitationInfo(resentToken);
    expect(info.email).toBe("eingeladen@example.com");
    await setupPassword(resentToken, "geheim-im-test", "Eingeladen Neu");
    expect(window.localStorage.getItem(DEMO_STORAGE_KEYS.data)).not.toContain("geheim-im-test");

    const token2 = await login("eingeladen@example.com", DEMO_PASSWORD);
    expect(token2.access_token).toMatch(/^demo\./);
  });
});
