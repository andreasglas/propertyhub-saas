import { AxiosError, AxiosHeaders } from "axios";
import type { AxiosResponse, InternalAxiosRequestConfig } from "axios";

import type { AccountingEntry } from "../services/accountingService";
import type { AuditLogEntry } from "../services/auditLogService";
import type { AuthUser, InvitationInfo } from "../services/authService";
import type { BankTransaction } from "../services/bankingService";
import type { Contract } from "../services/contractService";
import type { DocumentRecord } from "../services/documentService";
import type { Invoice } from "../services/invoiceService";
import type { OperatingCostItem, OperatingCostPeriod } from "../services/operatingCostService";
import type { Organization } from "../services/organizationService";
import type { Payment } from "../services/paymentService";
import type { Property } from "../services/propertyService";
import type { DashboardReport } from "../services/reportService";
import type {
  TaskComment,
  TaskHistoryEntry,
  TaskItem,
  TaskTemplate,
} from "../services/taskService";
import type { Tenant } from "../services/tenantService";
import type { Unit } from "../services/unitService";
import type { ManagedUser, UserInvitationResult } from "../services/userAdminService";
import type { Vendor } from "../services/vendorService";
import { DEMO_PASSWORD } from "./demoConfig";
import { createSimplePdf, toCsv } from "./demoExports";
import { createDateHelpers, DemoState, DemoUser, DEMO_ORGANIZATION_ID } from "./demoSeed";
import { buildSettlementPreview } from "./demoSettlement";
import { getDemoState, saveDemoState } from "./demoStore";

const DEMO_LATENCY_MS = import.meta.env.MODE === "test" ? 0 : 120;

export const DEMO_UNSUPPORTED_MESSAGE = "Diese Funktion ist im Demo-Modus nicht verfügbar.";

const TASK_PRIORITIES = ["low", "medium", "high", "urgent"];
const TASK_STATUSES = ["open", "in_progress", "blocked", "done", "cancelled"];
const TASK_CATEGORIES = [
  "maintenance",
  "inspection",
  "tenant_request",
  "accounting",
  "compliance",
  "other",
];
const TASK_FREQUENCIES = ["weekly", "monthly", "quarterly", "yearly"];
const ALLOCATION_METHODS = ["area", "unit_count", "occupancy_days", "advance_share"];
const DOCUMENT_MODELS = ["invoice", "property", "task"];
const OPEN_TASK_STATUSES = ["open", "in_progress", "blocked"];

/** Simulierte OCR-Laufzeiten (ms) – sichtbar über das bestehende Polling der Dokumentenansicht. */
export const DEMO_OCR_TIMINGS = { processingAfterMs: 1500, finishedAfterMs: 4000 };

export class DemoHttpError extends Error {
  constructor(
    readonly status: number,
    readonly detail: string,
  ) {
    super(detail);
  }
}

export type DemoRequest = {
  method: string;
  url: string;
  params?: Record<string, unknown> | null;
  data?: unknown;
  authorization?: string | null;
};

export type DemoReply = {
  status: number;
  data: unknown;
  contentType?: string;
};

type Context = {
  state: DemoState;
  method: string;
  params: Record<string, unknown>;
  body: unknown;
  authorization: string | null;
  now: Date;
};

type Handler = (context: Context, match: string[]) => DemoReply;

// ---------------------------------------------------------------------------
// Hilfsfunktionen

function ok(data: unknown, status = 200): DemoReply {
  return { status, data };
}

function fail(status: number, detail: string): never {
  throw new DemoHttpError(status, detail);
}

function randomHex(bytes: number) {
  const values = new Uint8Array(bytes);
  if (globalThis.crypto?.getRandomValues) {
    globalThis.crypto.getRandomValues(values);
  } else {
    for (let index = 0; index < values.length; index += 1) {
      values[index] = Math.floor(Math.random() * 256);
    }
  }
  return Array.from(values, (value) => value.toString(16).padStart(2, "0")).join("");
}

function newId() {
  const hex = randomHex(16);
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-4${hex.slice(13, 16)}-a${hex.slice(17, 20)}-${hex.slice(20, 32)}`;
}

function clone<T>(value: T): T {
  return value === undefined ? value : (JSON.parse(JSON.stringify(value)) as T);
}

function todayIso(now: Date) {
  return createDateHelpers(now).day(0);
}

function asRecord(body: unknown): Record<string, unknown> {
  if (body && typeof body === "object" && !(body instanceof FormData)) {
    return body as Record<string, unknown>;
  }
  return {};
}

function optionalString(value: unknown) {
  if (value === null || value === undefined) {
    return null;
  }
  const text = String(value).trim();
  return text ? text : null;
}

function requiredString(value: unknown, field: string) {
  const text = optionalString(value);
  if (!text) {
    fail(422, `Feld "${field}" ist erforderlich.`);
  }
  return text;
}

function requiredDate(value: unknown, field: string) {
  const text = requiredString(value, field);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(text)) {
    fail(422, `Feld "${field}" muss ein Datum (JJJJ-MM-TT) sein.`);
  }
  return text;
}

function optionalDate(value: unknown, field: string) {
  return optionalString(value) === null ? null : requiredDate(value, field);
}

function numberValue(value: unknown, field: string, { positive = false, optional = false } = {}) {
  if ((value === null || value === undefined || value === "") && optional) {
    return null;
  }
  const parsed = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(parsed)) {
    fail(422, `Feld "${field}" muss eine Zahl sein.`);
  }
  if (positive && parsed <= 0) {
    fail(422, `Feld "${field}" muss größer als 0 sein.`);
  }
  if (!positive && parsed < 0) {
    fail(422, `Feld "${field}" darf nicht negativ sein.`);
  }
  return parsed;
}

function requiredPositive(value: unknown, field: string) {
  return numberValue(value, field, { positive: true }) as number;
}

function oneOf(value: unknown, allowed: string[], field: string) {
  const text = String(value ?? "");
  if (!allowed.includes(text)) {
    fail(422, `Feld "${field}" muss einer der Werte ${allowed.join(", ")} sein.`);
  }
  return text;
}

function findOr404<T extends { id: string }>(items: T[], id: unknown, label: string) {
  const item = items.find((candidate) => candidate.id === id);
  if (!item) {
    fail(404, `${label} not found`);
  }
  return item;
}

function toManagedUser(user: DemoUser): ManagedUser {
  return {
    id: user.id,
    organization_id: user.organization_id,
    email: user.email,
    full_name: user.full_name ?? null,
    role: user.role,
    is_active: user.is_active,
    invitation_sent_at: user.invitation_sent_at ?? null,
    invitation_accepted_at: user.invitation_accepted_at ?? null,
  };
}

function toAuthUser(user: DemoUser): AuthUser {
  return {
    id: user.id,
    organization_id: user.organization_id,
    email: user.email,
    full_name: user.full_name ?? null,
    role: user.role,
    is_active: user.is_active,
  };
}

const TOKEN_PATTERN = /^demo\.([A-Za-z0-9-]+)\.[a-f0-9]{32}$/;

function currentUser(context: Context, roles?: string[]) {
  const header = context.authorization ?? "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : "";
  const userId = TOKEN_PATTERN.exec(token)?.[1];
  const user = context.state.users.find((candidate) => candidate.id === userId && candidate.is_active);
  if (!user) {
    fail(401, "Demo-Sitzung ungültig oder abgelaufen.");
  }
  if (roles && !roles.includes(user.role)) {
    fail(403, "Insufficient permissions for this action");
  }
  return user;
}

const MANAGERS = ["owner", "manager"];
const OWNERS = ["owner"];

function audit(
  context: Context,
  actor: DemoUser | null,
  action: string,
  resourceType: string,
  resourceId: string | null,
  summary: string,
  details: AuditLogEntry["details"] = null,
) {
  context.state.audit_logs.unshift({
    id: newId(),
    organization_id: DEMO_ORGANIZATION_ID,
    actor_user_id: actor?.id ?? null,
    actor_email: actor?.email ?? null,
    action,
    resource_type: resourceType,
    resource_id: resourceId,
    summary,
    details,
    created_at: context.now.toISOString(),
  });
}

function sortByDateDesc<T>(items: T[], pick: (item: T) => string | null | undefined) {
  return [...items].sort((left, right) => (pick(right) ?? "").localeCompare(pick(left) ?? ""));
}

function incrementDueDate(value: string, frequency: string) {
  const [year, month, day] = value.split("-").map(Number);
  if (frequency === "weekly") {
    return new Date(Date.UTC(year, month - 1, day + 7)).toISOString().slice(0, 10);
  }
  const monthsToAdd = frequency === "monthly" ? 1 : frequency === "quarterly" ? 3 : 12;
  const lastDay = new Date(Date.UTC(year, month - 1 + monthsToAdd + 1, 0)).getUTCDate();
  return new Date(Date.UTC(year, month - 1 + monthsToAdd, Math.min(day, lastDay)))
    .toISOString()
    .slice(0, 10);
}

function blobReply(content: string, contentType: string): DemoReply {
  return { status: 200, data: content, contentType };
}

// ---------------------------------------------------------------------------
// OCR-Simulation

function simulatedOcrResult(state: DemoState, document: DocumentRecord) {
  const invoice =
    document.related_model === "invoice"
      ? state.invoices.find((candidate) => candidate.id === document.related_id)
      : undefined;
  const stem = document.file_name.replace(/\.[^.]+$/, "").replace(/[-_]+/g, " ");
  const vendorName =
    invoice?.vendor_name ?? stem.replace(/\b\w/g, (character) => character.toUpperCase());
  const fields = {
    vendor_name: vendorName,
    invoice_number: invoice?.invoice_number ?? null,
    invoice_date: invoice?.invoice_date ?? null,
    gross_amount: invoice?.gross_amount ?? null,
  };
  const matched = Object.values(fields).filter((value) => value !== null).length;
  return {
    ...fields,
    confidence: Math.round((matched / 4) * 100) / 100,
    source: "demo_simulation",
    status: "processed",
  };
}

/** Schreitet simulierte OCR-Jobs zeitbasiert voran: queued → processing → processed/failed. */
export function advanceOcrJobs(state: DemoState, nowMs: number) {
  let changed = false;
  for (const [documentId, queuedAt] of Object.entries(state.ocr_jobs)) {
    const document = state.documents.find((candidate) => candidate.id === documentId);
    if (!document) {
      delete state.ocr_jobs[documentId];
      changed = true;
      continue;
    }
    const elapsed = nowMs - Date.parse(queuedAt);
    if (document.ocr_status === "queued" && elapsed >= DEMO_OCR_TIMINGS.processingAfterMs) {
      document.ocr_status = "processing";
      document.ocr_started_at = new Date(nowMs).toISOString();
      document.ocr_attempt_count += 1;
      changed = true;
    }
    if (document.ocr_status === "processing" && elapsed >= DEMO_OCR_TIMINGS.finishedAfterMs) {
      // Dateien mit "unscharf"/"unlesbar" im Namen scheitern beim ersten Versuch (Retry testbar).
      if (/unscharf|unlesbar|blurry/i.test(document.file_name) && document.ocr_attempt_count <= 1) {
        document.ocr_status = "failed";
        document.ocr_error = "Text konnte nicht zuverlässig erkannt werden (Demo-Simulation).";
        document.ocr_processed_at = null;
      } else {
        document.ocr_status = "processed";
        document.ocr_error = null;
        document.ocr_result = simulatedOcrResult(state, document);
        document.ocr_processed_at = new Date(nowMs).toISOString();
      }
      delete state.ocr_jobs[documentId];
      changed = true;
    }
  }
  return changed;
}

function queueOcr(context: Context, document: DocumentRecord) {
  document.ocr_status = "queued";
  document.ocr_error = null;
  document.ocr_started_at = null;
  document.ocr_processed_at = null;
  document.ocr_result = null;
  context.state.ocr_jobs[document.id] = context.now.toISOString();
}

// ---------------------------------------------------------------------------
// Fachliche Validierungen (analog zum Backend)

function ensureProperty(state: DemoState, propertyId: unknown) {
  if (!optionalString(propertyId)) {
    return null;
  }
  return findOr404(state.properties, propertyId, "Property");
}

function buildTaskFromPayload(state: DemoState, body: Record<string, unknown>) {
  const property = ensureProperty(state, body.property_id);
  let propertyId = property?.id ?? null;
  const unitId = optionalString(body.unit_id);
  if (unitId) {
    const unit = findOr404(state.units, unitId, "Unit");
    if (property && unit.property_id !== property.id) {
      fail(400, "Unit does not belong to selected property");
    }
    propertyId = unit.property_id;
  }
  const vendorId = optionalString(body.vendor_id);
  if (vendorId) {
    findOr404(state.vendors, vendorId, "Vendor");
  }
  return {
    property_id: propertyId,
    unit_id: unitId,
    vendor_id: vendorId,
    title: requiredString(body.title, "title"),
    description: optionalString(body.description),
    category: oneOf(body.category, TASK_CATEGORIES, "category"),
    priority: oneOf(body.priority, TASK_PRIORITIES, "priority"),
  };
}

function taskAuditDetails(task: TaskItem) {
  return {
    status: task.status,
    priority: task.priority,
    property_id: task.property_id ?? null,
    unit_id: task.unit_id ?? null,
    vendor_id: task.vendor_id ?? null,
    estimated_cost: task.estimated_cost ?? null,
    actual_cost: task.actual_cost ?? null,
    completed_at: task.completed_at ?? null,
  };
}

function writeTask(context: Context, body: Record<string, unknown>, existing?: TaskItem): TaskItem {
  const base = buildTaskFromPayload(context.state, body);
  const status = oneOf(body.status, TASK_STATUSES, "status");
  const recurringTemplateId = optionalString(body.recurring_template_id);
  if (recurringTemplateId) {
    findOr404(context.state.task_templates, recurringTemplateId, "Task template");
  }
  return {
    id: existing?.id ?? newId(),
    organization_id: DEMO_ORGANIZATION_ID,
    ...base,
    recurring_template_id: recurringTemplateId,
    status,
    due_date: optionalDate(body.due_date, "due_date"),
    estimated_cost: numberValue(body.estimated_cost, "estimated_cost", { optional: true }),
    actual_cost: numberValue(body.actual_cost, "actual_cost", { optional: true }),
    assignee_name: optionalString(body.assignee_name),
    completion_notes: optionalString(body.completion_notes),
    completed_at:
      status === "done" ? existing?.completed_at ?? context.now.toISOString() : null,
    source: optionalString(body.source) ?? "manual",
  };
}

function buildReport(state: DemoState, now: Date): DashboardReport {
  const today = todayIso(now);
  const sum = (values: Array<number | null | undefined>) =>
    Math.round(values.reduce<number>((total, value) => total + (value ?? 0), 0) * 100) / 100;
  const openTasks = state.tasks.filter((task) => OPEN_TASK_STATUSES.includes(task.status));
  return {
    properties_count: state.properties.length,
    units_count: state.units.length,
    tenants_count: state.tenants.length,
    contracts_count: state.contracts.length,
    invoices_count: state.invoices.length,
    open_invoices_count: state.invoices.filter((invoice) => invoice.status !== "paid").length,
    open_tasks_count: openTasks.length,
    overdue_tasks_count: openTasks.filter((task) => task.due_date && task.due_date < today).length,
    completed_tasks_count: state.tasks.filter((task) => task.status === "done").length,
    payments_count: state.payments.length,
    accounting_entries_count: state.accounting_entries.length,
    total_invoice_amount: sum(state.invoices.map((invoice) => invoice.gross_amount)),
    total_payment_amount: sum(state.payments.map((payment) => payment.amount)),
    total_income_amount: sum(
      state.accounting_entries.filter((entry) => entry.entry_type === "income").map((entry) => entry.amount),
    ),
    total_expense_amount: sum(
      state.accounting_entries.filter((entry) => entry.entry_type === "expense").map((entry) => entry.amount),
    ),
    total_estimated_task_cost: sum(state.tasks.map((task) => task.estimated_cost)),
    total_actual_task_cost: sum(state.tasks.map((task) => task.actual_cost)),
  };
}

function settlementPreviewFor(state: DemoState, periodId: string) {
  const period = findOr404(state.operating_cost_periods, periodId, "Operating cost period");
  const items = state.operating_cost_items.filter((item) => item.period_id === period.id);
  return buildSettlementPreview(period, items, state.units, state.contracts, state.tenants);
}

function invitationResult(user: DemoUser, token: string): UserInvitationResult {
  return {
    user: toManagedUser(user),
    invitation_token: token,
    // Basis-Pfad berücksichtigen, damit der Einladungslink auch unter GitHub Pages funktioniert.
    setup_path: `${import.meta.env.BASE_URL}setup-password?token=${encodeURIComponent(token)}`,
  };
}

// ---------------------------------------------------------------------------
// Routen

const routes: Array<{ method: string; pattern: RegExp; handler: Handler }> = [];

function route(method: string, path: string, handler: Handler) {
  const pattern = new RegExp(`^${path.replace(/:[a-zA-Z_]+/g, "([^/]+)")}$`);
  routes.push({ method, pattern, handler });
}

// Auth
route("post", "/auth/token", (context) => {
  const body =
    typeof context.body === "string"
      ? new URLSearchParams(context.body)
      : context.body instanceof URLSearchParams
        ? context.body
        : new URLSearchParams();
  const email = (body.get("username") ?? "").trim().toLowerCase();
  const password = body.get("password") ?? "";
  const user = context.state.users.find((candidate) => candidate.email.toLowerCase() === email);
  if (!user || !user.is_active || password !== DEMO_PASSWORD) {
    fail(401, "Invalid email or password");
  }
  return ok({ access_token: `demo.${user.id}.${randomHex(16)}`, token_type: "bearer" });
});

route("get", "/auth/me", (context) => ok(toAuthUser(currentUser(context))));

route("get", "/auth/invitations/:token", (context, [token]) => {
  const user = context.state.users.find((candidate) => candidate.invitation_token === token);
  if (!user) {
    fail(404, "Invitation token is invalid");
  }
  const info: InvitationInfo = {
    email: user.email,
    full_name: user.full_name ?? null,
    organization_name: context.state.organization.name,
    role: user.role,
  };
  return ok(info);
});

route("post", "/auth/setup-password", (context) => {
  const body = asRecord(context.body);
  const user = context.state.users.find(
    (candidate) => candidate.invitation_token && candidate.invitation_token === body.token,
  );
  if (!user) {
    fail(404, "Invitation token is invalid");
  }
  requiredString(body.password, "password");
  user.is_active = true;
  user.invitation_token = null;
  user.invitation_accepted_at = context.now.toISOString();
  const fullName = optionalString(body.full_name);
  if (fullName) {
    user.full_name = fullName;
  }
  audit(context, user, "user.invitation_accepted", "user", user.id, `Einladung von ${user.email} angenommen`, {
    role: user.role,
  });
  return ok({
    message: `Demo: Einladung angenommen. Anmeldung mit dem Demo-Passwort "${DEMO_PASSWORD}".`,
  });
});

// Organisation
route("get", "/organization/me", (context) => {
  currentUser(context);
  return ok(context.state.organization);
});

route("put", "/organization/me", (context) => {
  const actor = currentUser(context, OWNERS);
  const body = asRecord(context.body);
  const organization: Organization = {
    id: DEMO_ORGANIZATION_ID,
    name: requiredString(body.name, "name"),
    legal_name: optionalString(body.legal_name),
    street: optionalString(body.street),
    postal_code: optionalString(body.postal_code),
    city: optionalString(body.city),
    country: optionalString(body.country) ?? "Deutschland",
    contact_email: optionalString(body.contact_email),
    contact_phone: optionalString(body.contact_phone),
  };
  context.state.organization = organization;
  audit(context, actor, "organization.updated", "organization", organization.id, `Organisation ${organization.name} aktualisiert`);
  return ok(organization);
});

// Benutzer
route("get", "/users", (context) => {
  currentUser(context, MANAGERS);
  return ok(context.state.users.map(toManagedUser));
});

route("post", "/users", (context) => {
  const actor = currentUser(context, OWNERS);
  const body = asRecord(context.body);
  const email = requiredString(body.email, "email").toLowerCase();
  if (context.state.users.some((candidate) => candidate.email.toLowerCase() === email)) {
    fail(400, "User with this email already exists");
  }
  requiredString(body.password, "password");
  const user: DemoUser = {
    id: newId(),
    organization_id: DEMO_ORGANIZATION_ID,
    email,
    full_name: optionalString(body.full_name),
    role: oneOf(body.role, ["owner", "manager", "viewer"], "role"),
    is_active: body.is_active !== false,
    invitation_sent_at: null,
    invitation_accepted_at: context.now.toISOString(),
  };
  context.state.users.push(user);
  audit(context, actor, "user.created", "user", user.id, `Benutzer ${user.email} angelegt`, { role: user.role });
  return ok(toManagedUser(user), 201);
});

route("post", "/users/invitations", (context) => {
  const actor = currentUser(context, OWNERS);
  const body = asRecord(context.body);
  const email = requiredString(body.email, "email").toLowerCase();
  if (context.state.users.some((candidate) => candidate.email.toLowerCase() === email)) {
    fail(400, "User with this email already exists");
  }
  const token = `demo-invite-${randomHex(12)}`;
  const user: DemoUser = {
    id: newId(),
    organization_id: DEMO_ORGANIZATION_ID,
    email,
    full_name: optionalString(body.full_name),
    role: oneOf(body.role, ["owner", "manager", "viewer"], "role"),
    is_active: false,
    invitation_sent_at: context.now.toISOString(),
    invitation_accepted_at: null,
    invitation_token: token,
  };
  context.state.users.push(user);
  audit(context, actor, "user.invited", "user", user.id, `Einladung für ${user.email} erstellt`, {
    role: user.role,
    delivery: "demo_simulation",
  });
  return ok(invitationResult(user, token), 201);
});

route("put", "/users/:id", (context, [userId]) => {
  const actor = currentUser(context, OWNERS);
  const user = findOr404(context.state.users, userId, "User");
  const body = asRecord(context.body);
  user.full_name = optionalString(body.full_name);
  user.role = oneOf(body.role, ["owner", "manager", "viewer"], "role");
  user.is_active = body.is_active === true;
  // Passwortänderungen werden im Demo-Modus nicht gespeichert; es gilt immer das Demo-Passwort.
  audit(context, actor, "user.updated", "user", user.id, `Benutzer ${user.email} aktualisiert`, {
    role: user.role,
    is_active: user.is_active,
  });
  return ok(toManagedUser(user));
});

route("post", "/users/:id/invite", (context, [userId]) => {
  const actor = currentUser(context, OWNERS);
  const user = findOr404(context.state.users, userId, "User");
  if (user.invitation_accepted_at) {
    fail(400, "Invitation has already been accepted");
  }
  const token = `demo-invite-${randomHex(12)}`;
  user.invitation_token = token;
  user.invitation_sent_at = context.now.toISOString();
  user.is_active = false;
  audit(context, actor, "user.reinvited", "user", user.id, `Einladung für ${user.email} erneut versendet`, {
    delivery: "demo_simulation",
  });
  return ok(invitationResult(user, token));
});

// Stammdaten
route("get", "/properties", (context) => {
  currentUser(context);
  return ok(context.state.properties);
});

route("post", "/properties", (context) => {
  const actor = currentUser(context, MANAGERS);
  const body = asRecord(context.body);
  const property: Property = {
    id: newId(),
    organization_id: DEMO_ORGANIZATION_ID,
    name: requiredString(body.name, "name"),
    property_type: requiredString(body.property_type, "property_type"),
    street: optionalString(body.street),
    city: optionalString(body.city),
    postal_code: optionalString(body.postal_code),
    purchase_price: numberValue(body.purchase_price, "purchase_price", { optional: true }),
  };
  context.state.properties.unshift(property);
  audit(context, actor, "property.created", "property", property.id, `Immobilie ${property.name} angelegt`);
  return ok(property, 201);
});

route("get", "/units", (context) => {
  currentUser(context);
  return ok(context.state.units);
});

route("post", "/units", (context) => {
  const actor = currentUser(context, MANAGERS);
  const body = asRecord(context.body);
  const property = findOr404(context.state.properties, body.property_id, "Property");
  const unit: Unit = {
    id: newId(),
    organization_id: DEMO_ORGANIZATION_ID,
    property_id: property.id,
    name: requiredString(body.name, "name"),
    unit_type: requiredString(body.unit_type, "unit_type"),
    status: requiredString(body.status, "status"),
    area_sqm: numberValue(body.area_sqm, "area_sqm", { optional: true }),
  };
  context.state.units.unshift(unit);
  audit(context, actor, "unit.created", "unit", unit.id, `Einheit ${unit.name} angelegt`);
  return ok(unit, 201);
});

route("get", "/tenants", (context) => {
  currentUser(context);
  return ok(context.state.tenants);
});

route("post", "/tenants", (context) => {
  const actor = currentUser(context, MANAGERS);
  const body = asRecord(context.body);
  const tenant: Tenant = {
    id: newId(),
    organization_id: DEMO_ORGANIZATION_ID,
    first_name: requiredString(body.first_name, "first_name"),
    last_name: requiredString(body.last_name, "last_name"),
    email: optionalString(body.email),
    phone: optionalString(body.phone),
    move_in_date: optionalDate(body.move_in_date, "move_in_date"),
    move_out_date: optionalDate(body.move_out_date, "move_out_date"),
  };
  context.state.tenants.unshift(tenant);
  audit(context, actor, "tenant.created", "tenant", tenant.id, `Mieter ${tenant.first_name} ${tenant.last_name} angelegt`);
  return ok(tenant, 201);
});

route("get", "/contracts", (context) => {
  currentUser(context);
  return ok(context.state.contracts);
});

route("post", "/contracts", (context) => {
  const actor = currentUser(context, MANAGERS);
  const body = asRecord(context.body);
  const unit = findOr404(context.state.units, body.unit_id, "Unit");
  const tenant = findOr404(context.state.tenants, body.tenant_id, "Tenant");
  const startDate = requiredDate(body.start_date, "start_date");
  const endDate = optionalDate(body.end_date, "end_date");
  if (endDate && endDate < startDate) {
    fail(422, "end_date must be on or after start_date");
  }
  const contract: Contract = {
    id: newId(),
    organization_id: DEMO_ORGANIZATION_ID,
    unit_id: unit.id,
    tenant_id: tenant.id,
    start_date: startDate,
    end_date: endDate,
    cold_rent: numberValue(body.cold_rent, "cold_rent") as number,
    service_charge_advance: numberValue(body.service_charge_advance, "service_charge_advance") as number,
  };
  context.state.contracts.unshift(contract);
  audit(context, actor, "contract.created", "contract", contract.id, `Vertrag ${contract.id} angelegt`);
  return ok(contract, 201);
});

route("get", "/vendors", (context) => {
  currentUser(context);
  return ok([...context.state.vendors].sort((left, right) => left.name.localeCompare(right.name)));
});

route("post", "/vendors", (context) => {
  const actor = currentUser(context, MANAGERS);
  const body = asRecord(context.body);
  const vendor: Vendor = {
    id: newId(),
    organization_id: DEMO_ORGANIZATION_ID,
    name: requiredString(body.name, "name"),
    service_type: requiredString(body.service_type, "service_type"),
    contact_email: optionalString(body.contact_email),
    contact_phone: optionalString(body.contact_phone),
    notes: optionalString(body.notes),
  };
  context.state.vendors.push(vendor);
  audit(context, actor, "vendor.created", "vendor", vendor.id, `Dienstleister ${vendor.name} angelegt`);
  return ok(vendor, 201);
});

// Finanzen
route("get", "/invoices", (context) => {
  currentUser(context);
  return ok(context.state.invoices);
});

route("post", "/invoices", (context) => {
  const actor = currentUser(context, MANAGERS);
  const body = asRecord(context.body);
  const property = ensureProperty(context.state, body.property_id);
  const invoice: Invoice = {
    id: newId(),
    organization_id: DEMO_ORGANIZATION_ID,
    property_id: property?.id ?? null,
    vendor_name: requiredString(body.vendor_name, "vendor_name"),
    invoice_number: optionalString(body.invoice_number),
    invoice_date: optionalDate(body.invoice_date, "invoice_date"),
    gross_amount: requiredPositive(body.gross_amount, "gross_amount"),
    status: requiredString(body.status, "status"),
  };
  context.state.invoices.unshift(invoice);
  audit(context, actor, "invoice.created", "invoice", invoice.id, `Rechnung ${invoice.invoice_number ?? invoice.id} angelegt`);
  return ok(invoice, 201);
});

route("get", "/payments", (context) => {
  currentUser(context);
  return ok(context.state.payments);
});

route("post", "/payments", (context) => {
  const actor = currentUser(context, MANAGERS);
  const body = asRecord(context.body);
  const invoiceId = optionalString(body.invoice_id);
  const contractId = optionalString(body.contract_id);
  if (!invoiceId && !contractId) {
    fail(422, "invoice_id or contract_id must be provided");
  }
  if (invoiceId) {
    findOr404(context.state.invoices, invoiceId, "Invoice");
  }
  if (contractId) {
    findOr404(context.state.contracts, contractId, "Contract");
  }
  const payment: Payment = {
    id: newId(),
    organization_id: DEMO_ORGANIZATION_ID,
    invoice_id: invoiceId,
    contract_id: contractId,
    amount: requiredPositive(body.amount, "amount"),
    booking_date: optionalDate(body.booking_date, "booking_date"),
    reference: optionalString(body.reference),
  };
  context.state.payments.unshift(payment);
  audit(context, actor, "payment.created", "payment", payment.id, `Zahlung ${payment.id} angelegt`);
  return ok(payment, 201);
});

route("get", "/accounting", (context) => {
  currentUser(context);
  return ok(context.state.accounting_entries);
});

route("post", "/accounting", (context) => {
  const actor = currentUser(context, MANAGERS);
  const body = asRecord(context.body);
  const property = ensureProperty(context.state, body.property_id);
  const entry: AccountingEntry = {
    id: newId(),
    organization_id: DEMO_ORGANIZATION_ID,
    property_id: property?.id ?? null,
    entry_type: requiredString(body.entry_type, "entry_type"),
    category: optionalString(body.category),
    amount: requiredPositive(body.amount, "amount"),
    booking_date: optionalDate(body.booking_date, "booking_date"),
  };
  context.state.accounting_entries.unshift(entry);
  audit(context, actor, "accounting.created", "accounting_entry", entry.id, `Accounting-Eintrag ${entry.id} angelegt`);
  return ok(entry, 201);
});

// Banking
route("get", "/banking", (context) => {
  currentUser(context);
  return ok(sortByDateDesc(context.state.bank_transactions, (transaction) => transaction.booking_date));
});

route("post", "/banking/import-stub", (context) => {
  const actor = currentUser(context, MANAGERS);
  const today = todayIso(context.now);
  const contract = context.state.contracts.find((candidate) => candidate.id === "demo-con-schneider");
  const sequence = context.state.sequence++;
  const transactions: BankTransaction[] = [
    {
      id: newId(),
      organization_id: DEMO_ORGANIZATION_ID,
      payment_id: null,
      external_id: `demo-stub-${sequence}-001`,
      account_name: "Mietkonto (Demo)",
      transaction_type: "credit",
      booking_date: today,
      value_date: today,
      amount: contract ? contract.cold_rent + contract.service_charge_advance : 970,
      currency: "EUR",
      counterparty_name: "Anna Schneider",
      iban: "DE00 0000 0000 0000 0000 00",
      reference: "Miete aktueller Monat WE 1.1 EG links",
      status: "imported",
    },
    {
      id: newId(),
      organization_id: DEMO_ORGANIZATION_ID,
      payment_id: null,
      external_id: `demo-stub-${sequence}-002`,
      account_name: "Geschäftskonto (Demo)",
      transaction_type: "debit",
      booking_date: today,
      value_date: today,
      amount: 420,
      currency: "EUR",
      counterparty_name: "Hansewerk Energie (Demo)",
      iban: "DE00 0000 0000 0000 0000 03",
      reference: "Abschlag Energie",
      status: "imported",
    },
  ];
  context.state.bank_transactions.unshift(...transactions);
  audit(context, actor, "bank_transaction.stub_imported", "bank_transaction", null, "Stub-Banktransaktionen importiert", {
    imported_count: transactions.length,
    source: "demo_simulation",
  });
  return ok({ imported_count: transactions.length, transactions });
});

route("post", "/banking/transactions/:id/match-payment", (context, [transactionId]) => {
  const actor = currentUser(context, MANAGERS);
  const body = asRecord(context.body);
  const payment = findOr404(context.state.payments, body.payment_id, "Payment");
  const transaction = findOr404(context.state.bank_transactions, transactionId, "Bank transaction");
  transaction.payment_id = payment.id;
  transaction.status = "matched";
  audit(context, actor, "bank_transaction.matched", "bank_transaction", transaction.id, `Banktransaktion ${transaction.id} mit Zahlung verknüpft`, {
    payment_id: payment.id,
  });
  return ok(transaction);
});

// Betriebskosten
route("get", "/operating-costs/periods", (context) => {
  currentUser(context);
  return ok(context.state.operating_cost_periods);
});

route("post", "/operating-costs/periods", (context) => {
  const actor = currentUser(context, MANAGERS);
  const body = asRecord(context.body);
  const property = findOr404(context.state.properties, body.property_id, "Property");
  const periodStart = requiredDate(body.period_start, "period_start");
  const periodEnd = requiredDate(body.period_end, "period_end");
  if (periodEnd < periodStart) {
    fail(422, "period_end must be on or after period_start");
  }
  const period: OperatingCostPeriod = {
    id: newId(),
    organization_id: DEMO_ORGANIZATION_ID,
    property_id: property.id,
    name: requiredString(body.name, "name"),
    period_start: periodStart,
    period_end: periodEnd,
    status: optionalString(body.status) ?? "draft",
  };
  context.state.operating_cost_periods.unshift(period);
  audit(context, actor, "operating_cost_period.created", "operating_cost_period", period.id, `Nebenkostenperiode ${period.name} angelegt`);
  return ok(period, 201);
});

route("get", "/operating-costs/periods/:id/items", (context, [periodId]) => {
  currentUser(context);
  findOr404(context.state.operating_cost_periods, periodId, "Operating cost period");
  return ok(context.state.operating_cost_items.filter((item) => item.period_id === periodId));
});

route("post", "/operating-costs/periods/:id/items", (context, [periodId]) => {
  const actor = currentUser(context, MANAGERS);
  const period = findOr404(context.state.operating_cost_periods, periodId, "Operating cost period");
  const body = asRecord(context.body);
  const item: OperatingCostItem = {
    id: newId(),
    organization_id: DEMO_ORGANIZATION_ID,
    period_id: period.id,
    category: requiredString(body.category, "category"),
    description: optionalString(body.description),
    allocation_method: oneOf(body.allocation_method, ALLOCATION_METHODS, "allocation_method"),
    amount: requiredPositive(body.amount, "amount"),
    billable: body.billable !== false,
  };
  context.state.operating_cost_items.unshift(item);
  audit(context, actor, "operating_cost_item.created", "operating_cost_item", item.id, `Nebenkostenposition ${item.category} angelegt`);
  return ok(item, 201);
});

route("get", "/operating-costs/periods/:id/settlement-preview", (context, [periodId]) => {
  currentUser(context);
  return ok(settlementPreviewFor(context.state, periodId));
});

route("post", "/operating-costs/periods/:id/finalize", (context, [periodId]) => {
  const actor = currentUser(context, MANAGERS);
  const period = findOr404(context.state.operating_cost_periods, periodId, "Operating cost period");
  period.status = "finalized";
  audit(context, actor, "operating_cost_period.finalized", "operating_cost_period", period.id, `Nebenkostenperiode ${period.name} finalisiert`);
  return ok(period);
});

route("get", "/operating-costs/periods/:id/export.csv", (context, [periodId]) => {
  const actor = currentUser(context);
  const preview = settlementPreviewFor(context.state, periodId);
  const rows: unknown[][] = [
    ["period", preview.period.name],
    ["property_id", preview.period.property_id],
    ["period_start", preview.period.period_start],
    ["period_end", preview.period.period_end],
    ["status", preview.period.status],
    [],
    ["items"],
    ["category", "description", "allocation_method", "amount", "billable"],
    ...preview.items.map((item) => [item.category, item.description ?? "", item.allocation_method, item.amount, item.billable]),
    [],
    ["settlement_lines"],
    ["line_type", "tenant_name", "unit_name", "occupied_days", "allocation_factor", "share_amount", "advance_paid_amount", "balance_amount"],
    ...preview.lines.map((line) => [
      line.line_type,
      line.tenant_name ?? "",
      line.unit_name,
      line.occupied_days,
      line.allocation_factor,
      line.share_amount,
      line.advance_paid_amount,
      line.balance_amount,
    ]),
  ];
  audit(context, actor, "operating_cost_period.exported_csv", "operating_cost_period", preview.period.id, `Nebenkostenabrechnung ${preview.period.name} als CSV exportiert`);
  return blobReply(toCsv(rows), "text/csv");
});

route("get", "/operating-costs/periods/:id/export.pdf", (context, [periodId]) => {
  const actor = currentUser(context);
  const preview = settlementPreviewFor(context.state, periodId);
  const property = context.state.properties.find((candidate) => candidate.id === preview.period.property_id);
  const euro = (value: number) => `${value.toFixed(2)} EUR`;
  const lines = [
    `Nebenkostenabrechnung ${preview.period.name} (DEMO - fiktive Daten)`,
    `Objekt: ${property?.name ?? preview.period.property_id}`,
    `Zeitraum: ${preview.period.period_start} bis ${preview.period.period_end} · Status: ${preview.period.status}`,
    "",
    `Umlagefähige Kosten: ${euro(preview.total_billable_amount)} · Vorauszahlungen: ${euro(preview.total_advance_amount)}`,
    "",
    "Kostenpositionen:",
    ...preview.items.map(
      (item) =>
        `- ${item.category}: ${euro(item.amount)} · ${item.allocation_method} · ${item.billable ? "umlagefähig" : "nicht umlagefähig"}`,
    ),
    "",
    "Abrechnung je Einheit:",
    ...preview.lines.map(
      (line) =>
        `- ${line.tenant_name ?? "Leerstand"} · ${line.unit_name} · ${line.occupied_days} Tage · Anteil ${euro(line.share_amount)} · Saldo ${euro(line.balance_amount)}`,
    ),
  ];
  audit(context, actor, "operating_cost_period.exported_pdf", "operating_cost_period", preview.period.id, `Nebenkostenabrechnung ${preview.period.name} als PDF exportiert`);
  return blobReply(createSimplePdf(lines), "application/pdf");
});

// Aufgaben (feste Pfade vor Pfaden mit IDs registrieren)
route("get", "/tasks/templates", (context) => {
  currentUser(context);
  return ok(context.state.task_templates);
});

route("post", "/tasks/templates", (context) => {
  const actor = currentUser(context, MANAGERS);
  const body = asRecord(context.body);
  const base = buildTaskFromPayload(context.state, body);
  const template: TaskTemplate = {
    id: newId(),
    organization_id: DEMO_ORGANIZATION_ID,
    ...base,
    recurrence_frequency: oneOf(body.recurrence_frequency, TASK_FREQUENCIES, "recurrence_frequency"),
    next_due_date: requiredDate(body.next_due_date, "next_due_date"),
    assignee_name: optionalString(body.assignee_name),
    active: body.active !== false,
  };
  context.state.task_templates.unshift(template);
  audit(context, actor, "task_template.created", "task_template", template.id, `Wiederkehrende Aufgabe ${template.title} angelegt`, {
    frequency: template.recurrence_frequency,
    next_due_date: template.next_due_date,
  });
  return ok(template, 201);
});

route("post", "/tasks/templates/generate-due", (context) => {
  const actor = currentUser(context, MANAGERS);
  const today = todayIso(context.now);
  const generated: TaskItem[] = [];
  for (const template of context.state.task_templates) {
    if (!template.active || template.next_due_date > today) {
      continue;
    }
    generated.push({
      id: newId(),
      organization_id: DEMO_ORGANIZATION_ID,
      property_id: template.property_id ?? null,
      unit_id: template.unit_id ?? null,
      vendor_id: template.vendor_id ?? null,
      recurring_template_id: template.id,
      title: template.title,
      description: template.description ?? null,
      category: template.category,
      priority: template.priority,
      status: "open",
      due_date: template.next_due_date,
      estimated_cost: null,
      actual_cost: null,
      assignee_name: template.assignee_name ?? null,
      completion_notes: null,
      completed_at: null,
      source: "recurring",
    });
    template.next_due_date = incrementDueDate(template.next_due_date, template.recurrence_frequency);
  }
  context.state.tasks.unshift(...generated);
  if (generated.length) {
    audit(context, actor, "task_template.generated", "task_template", null, `${generated.length} wiederkehrende Aufgaben erzeugt`, {
      task_ids: generated.map((task) => task.id).join(","),
    });
  }
  return ok({ generated_count: generated.length, tasks: generated });
});

route("get", "/tasks", (context) => {
  currentUser(context);
  return ok(context.state.tasks);
});

route("post", "/tasks", (context) => {
  const actor = currentUser(context, MANAGERS);
  const task = writeTask(context, asRecord(context.body));
  context.state.tasks.unshift(task);
  audit(context, actor, "task.created", "task", task.id, `Aufgabe ${task.title} angelegt`, taskAuditDetails(task));
  return ok(task, 201);
});

route("put", "/tasks/:id", (context, [taskId]) => {
  const actor = currentUser(context, MANAGERS);
  const existing = findOr404(context.state.tasks, taskId, "Task");
  const task = writeTask(context, asRecord(context.body), existing);
  context.state.tasks = context.state.tasks.map((candidate) => (candidate.id === task.id ? task : candidate));
  audit(context, actor, "task.updated", "task", task.id, `Aufgabe ${task.title} aktualisiert`, taskAuditDetails(task));
  return ok(task);
});

route("delete", "/tasks/:id", (context, [taskId]) => {
  const actor = currentUser(context, MANAGERS);
  const task = findOr404(context.state.tasks, taskId, "Task");
  context.state.tasks = context.state.tasks.filter((candidate) => candidate.id !== task.id);
  context.state.task_comments = context.state.task_comments.filter((comment) => comment.task_id !== task.id);
  audit(context, actor, "task.deleted", "task", task.id, `Aufgabe ${task.title} gelöscht`, taskAuditDetails(task));
  return ok(null, 204);
});

route("get", "/tasks/:id/comments", (context, [taskId]) => {
  currentUser(context);
  findOr404(context.state.tasks, taskId, "Task");
  return ok(
    sortByDateDesc(
      context.state.task_comments.filter((comment) => comment.task_id === taskId),
      (comment) => comment.created_at,
    ),
  );
});

route("post", "/tasks/:id/comments", (context, [taskId]) => {
  const actor = currentUser(context, MANAGERS);
  const task = findOr404(context.state.tasks, taskId, "Task");
  const comment: TaskComment = {
    id: newId(),
    organization_id: DEMO_ORGANIZATION_ID,
    task_id: task.id,
    author_user_id: actor.id,
    author_email: actor.email,
    message: requiredString(asRecord(context.body).message, "message"),
    created_at: context.now.toISOString(),
  };
  context.state.task_comments.push(comment);
  return ok(comment, 201);
});

function taskAttachments(state: DemoState, taskId: string) {
  return sortByDateDesc(
    state.documents.filter((document) => document.related_model === "task" && document.related_id === taskId),
    (document) => document.created_at,
  );
}

route("get", "/tasks/:id/attachments", (context, [taskId]) => {
  currentUser(context);
  findOr404(context.state.tasks, taskId, "Task");
  return ok(taskAttachments(context.state, taskId));
});

route("get", "/tasks/:id/history", (context, [taskId]) => {
  currentUser(context);
  findOr404(context.state.tasks, taskId, "Task");
  const entries: TaskHistoryEntry[] = [
    ...context.state.audit_logs
      .filter((entry) => entry.resource_type === "task" && entry.resource_id === taskId)
      .map((entry) => ({
        entry_type: "audit",
        entry_id: entry.id,
        created_at: entry.created_at,
        actor_email: entry.actor_email ?? null,
        title: entry.action,
        message: entry.summary,
        metadata: entry.details ?? null,
      })),
    ...context.state.task_comments
      .filter((comment) => comment.task_id === taskId)
      .map((comment) => ({
        entry_type: "comment",
        entry_id: comment.id,
        created_at: comment.created_at,
        actor_email: comment.author_email ?? null,
        title: "Kommentar",
        message: comment.message,
        metadata: { task_id: comment.task_id },
      })),
    ...taskAttachments(context.state, taskId).map((document) => ({
      entry_type: "attachment",
      entry_id: document.id,
      created_at: document.created_at ?? "",
      actor_email: null,
      title: "Anhang",
      message: `Anhang ${document.file_name} hochgeladen`,
      metadata: { document_type: document.document_type, document_id: document.id },
    })),
  ];
  return ok(sortByDateDesc(entries, (entry) => entry.created_at));
});

// Dokumente & OCR
route("get", "/documents", (context) => {
  currentUser(context);
  return ok(sortByDateDesc(context.state.documents, (document) => document.created_at));
});

route("post", "/documents/upload", (context) => {
  const actor = currentUser(context, MANAGERS);
  if (!(context.body instanceof FormData)) {
    fail(422, "Multipart-Formular erwartet.");
  }
  const form = context.body;
  const relatedModel = oneOf(form.get("related_model"), DOCUMENT_MODELS, "related_model");
  const relatedId = requiredString(form.get("related_id"), "related_id");
  const collection =
    relatedModel === "invoice"
      ? context.state.invoices
      : relatedModel === "property"
        ? context.state.properties
        : context.state.tasks;
  findOr404<{ id: string }>(collection, relatedId, relatedModel.charAt(0).toUpperCase() + relatedModel.slice(1));
  const file = form.get("file");
  if (!(file instanceof Blob) || file.size === 0) {
    fail(400, "Uploaded file is empty");
  }
  const fileName = (file instanceof File && file.name ? file.name : "document.bin").split(/[\\/]/).pop() ?? "document.bin";
  // Die Datei verlässt den Browser nicht: es werden nur Metadaten im Demo-Bestand gespeichert.
  const document: DocumentRecord = {
    id: newId(),
    organization_id: DEMO_ORGANIZATION_ID,
    created_at: context.now.toISOString(),
    related_model: relatedModel,
    related_id: relatedId,
    document_type: requiredString(form.get("document_type"), "document_type"),
    file_name: fileName,
    storage_path: null,
    ocr_status: "pending",
    ocr_error: null,
    ocr_attempt_count: 0,
    ocr_started_at: null,
    ocr_result: null,
    ocr_processed_at: null,
  };
  context.state.documents.unshift(document);
  audit(context, actor, "document.uploaded", "document", document.id, `Dokument ${document.file_name} hochgeladen`, {
    storage: "demo_metadata_only",
  });
  return ok(document, 201);
});

route("post", "/documents/:id/process-ocr", (context, [documentId]) => {
  const actor = currentUser(context, MANAGERS);
  const document = findOr404(context.state.documents, documentId, "Document");
  if (["queued", "processing"].includes(document.ocr_status)) {
    fail(409, "OCR processing is already in progress");
  }
  queueOcr(context, document);
  audit(context, actor, "document.ocr_queued", "document", document.id, `OCR für Dokument ${document.file_name} angestoßen`);
  return ok({ document });
});

route("post", "/documents/:id/retry-ocr", (context, [documentId]) => {
  const actor = currentUser(context, MANAGERS);
  const document = findOr404(context.state.documents, documentId, "Document");
  if (document.ocr_status !== "failed") {
    fail(400, "Only failed OCR jobs can be retried");
  }
  queueOcr(context, document);
  audit(context, actor, "document.ocr_retried", "document", document.id, `OCR für Dokument ${document.file_name} erneut angestoßen`);
  return ok({ document });
});

route("post", "/documents/:id/apply-ocr-to-invoice", (context, [documentId]) => {
  const actor = currentUser(context, MANAGERS);
  const document = findOr404(context.state.documents, documentId, "Document");
  if (document.related_model !== "invoice") {
    fail(400, "OCR application is only supported for invoice documents");
  }
  if (document.ocr_status !== "processed" || !document.ocr_result) {
    fail(400, "Document OCR must be processed first");
  }
  const invoice = findOr404(context.state.invoices, document.related_id, "Invoice");
  const result = document.ocr_result;
  if (typeof result.vendor_name === "string" && result.vendor_name.trim()) {
    invoice.vendor_name = result.vendor_name.trim();
  }
  if (typeof result.invoice_number === "string" && result.invoice_number.trim()) {
    invoice.invoice_number = result.invoice_number.trim();
  }
  if (typeof result.invoice_date === "string" && result.invoice_date.trim()) {
    invoice.invoice_date = result.invoice_date;
  }
  if (typeof result.gross_amount === "number" && result.gross_amount > 0) {
    invoice.gross_amount = result.gross_amount;
  }
  if (invoice.status === "draft") {
    invoice.status = "received";
  }
  audit(context, actor, "document.ocr_applied", "document", document.id, `OCR-Daten aus Dokument ${document.file_name} auf Rechnung angewendet`, {
    invoice_id: invoice.id,
  });
  return ok({ document, invoice });
});

// Berichte & Audit-Log
route("get", "/reports", (context) => {
  currentUser(context);
  return ok(buildReport(context.state, context.now));
});

route("get", "/reports/export/tasks.csv", (context) => {
  currentUser(context);
  const today = todayIso(context.now);
  const names = (items: Array<{ id: string; name: string }>) => new Map(items.map((item) => [item.id, item.name]));
  const propertyNames = names(context.state.properties);
  const unitNames = names(context.state.units);
  const vendorNames = names(context.state.vendors);
  const rows: unknown[][] = [
    ["task_id", "title", "property_name", "unit_name", "vendor_name", "category", "priority", "status", "due_date", "completed_at", "estimated_cost", "actual_cost", "days_overdue", "source"],
    ...context.state.tasks.map((task) => {
      const overdue =
        task.due_date && OPEN_TASK_STATUSES.includes(task.status) && task.due_date < today
          ? Math.round((Date.parse(today) - Date.parse(task.due_date)) / 86400000)
          : 0;
      return [
        task.id,
        task.title,
        propertyNames.get(task.property_id ?? ""),
        unitNames.get(task.unit_id ?? ""),
        vendorNames.get(task.vendor_id ?? ""),
        task.category,
        task.priority,
        task.status,
        task.due_date,
        task.completed_at,
        task.estimated_cost,
        task.actual_cost,
        overdue,
        task.source,
      ];
    }),
  ];
  return blobReply(toCsv(rows), "text/csv");
});

route("get", "/audit-logs", (context) => {
  currentUser(context);
  const action = optionalString(context.params.action);
  const resourceType = optionalString(context.params.resource_type);
  const limit = Math.min(Math.max(Number(context.params.limit ?? 100) || 100, 1), 500);
  return ok(
    sortByDateDesc(context.state.audit_logs, (entry) => entry.created_at)
      .filter((entry) => (!action || entry.action === action) && (!resourceType || entry.resource_type === resourceType))
      .slice(0, limit),
  );
});

// ---------------------------------------------------------------------------
// Einstieg

function normalizePath(url: string) {
  let path = url.split("?")[0] ?? "";
  path = path.replace(/^[a-z]+:\/\/[^/]+/i, "");
  path = path.replace(/^\/api(\/v1)?(?=\/)/, "");
  if (!path.startsWith("/")) {
    path = `/${path}`;
  }
  if (path.length > 1 && path.endsWith("/")) {
    path = path.slice(0, -1);
  }
  return path;
}

function parseBody(data: unknown) {
  if (typeof data !== "string") {
    return data;
  }
  try {
    return JSON.parse(data) as unknown;
  } catch {
    return data;
  }
}

/**
 * Beantwortet einen API-Request vollständig lokal aus dem Demo-Bestand.
 * Änderungen werden nur bei Erfolg übernommen und im Browser gespeichert.
 */
export function handleDemoRequest(request: DemoRequest, now: Date = new Date()): DemoReply {
  const method = request.method.toLowerCase();
  const path = normalizePath(request.url);
  const stored = getDemoState();
  const state = clone(stored);
  const ocrChanged = advanceOcrJobs(state, now.getTime());
  const context: Context = {
    state,
    method,
    params: request.params ?? {},
    body: parseBody(request.data),
    authorization: request.authorization ?? null,
    now,
  };

  const matchedRoute = routes.find(
    (candidate) => candidate.method === method && candidate.pattern.test(path),
  );
  if (!matchedRoute) {
    if (ocrChanged) {
      saveDemoState(state);
    }
    console.warn(`[PropertyHub Demo] Nicht unterstützte Operation: ${method.toUpperCase()} ${path}`);
    return { status: 501, data: { detail: DEMO_UNSUPPORTED_MESSAGE, demo: true } };
  }

  const match = (matchedRoute.pattern.exec(path) ?? []).slice(1).map((value) => decodeURIComponent(value));
  try {
    const reply = matchedRoute.handler(context, match);
    if (method !== "get" || ocrChanged || reply.contentType) {
      saveDemoState(state);
    }
    return { ...reply, data: reply.contentType ? reply.data : clone(reply.data) };
  } catch (error) {
    if (ocrChanged) {
      const persisted = clone(stored);
      advanceOcrJobs(persisted, now.getTime());
      saveDemoState(persisted);
    }
    if (error instanceof DemoHttpError) {
      return { status: error.status, data: { detail: error.detail, demo: true } };
    }
    throw error;
  }
}

function sleep(milliseconds: number) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

/** Axios-Adapter: ersetzt im Demo-Modus jeden Netzwerkzugriff des zentralen API-Clients. */
export async function demoAdapter(config: InternalAxiosRequestConfig): Promise<AxiosResponse> {
  if (DEMO_LATENCY_MS) {
    await sleep(DEMO_LATENCY_MS);
  }
  const authorization = AxiosHeaders.from(config.headers).get("Authorization");
  const reply = handleDemoRequest({
    method: config.method ?? "get",
    url: config.url ?? "/",
    params: (config.params as Record<string, unknown> | undefined) ?? null,
    data: config.data,
    authorization: typeof authorization === "string" ? authorization : null,
  });

  const data =
    reply.contentType && config.responseType === "blob"
      ? new Blob([String(reply.data)], { type: reply.contentType })
      : reply.data;
  const response: AxiosResponse = {
    data,
    status: reply.status,
    statusText: reply.status < 400 ? "OK" : "Demo Error",
    headers: AxiosHeaders.from({
      "content-type": reply.contentType ?? "application/json",
      "x-propertyhub-demo": "true",
    }),
    config,
    request: { demo: true },
  };

  if (reply.status >= 200 && reply.status < 300) {
    return response;
  }
  const detail =
    reply.data && typeof reply.data === "object" && "detail" in reply.data
      ? String((reply.data as { detail: unknown }).detail)
      : "Demo-Fehler";
  throw new AxiosError(
    detail,
    reply.status >= 500 ? AxiosError.ERR_BAD_RESPONSE : AxiosError.ERR_BAD_REQUEST,
    config,
    response.request,
    response,
  );
}
