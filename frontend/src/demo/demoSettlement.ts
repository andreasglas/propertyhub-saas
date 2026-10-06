import type { Contract } from "../services/contractService";
import type {
  OperatingCostItem,
  OperatingCostPeriod,
  OperatingCostSettlementLine,
  OperatingCostSettlementPreview,
} from "../services/operatingCostService";
import type { Tenant } from "../services/tenantService";
import type { Unit } from "../services/unitService";

const DAY_MS = 24 * 60 * 60 * 1000;

type Segment = {
  lineKey: string;
  lineType: "contract" | "vacancy";
  contract: Contract | null;
  tenant: Tenant | null;
  unit: Unit;
  occupiedDays: number;
  areaSqm: number;
  advancePaid: number;
};

function toDay(value: string) {
  return Math.round(Date.parse(`${value}T00:00:00Z`) / DAY_MS);
}

function daysBetween(start: number, end: number) {
  return end - start + 1;
}

function roundCurrency(value: number) {
  return Math.round(value * 100) / 100;
}

function proratedAdvance(monthlyAdvance: number, start: number, end: number) {
  let total = 0;
  const startDate = new Date(start * DAY_MS);
  const endDate = new Date(end * DAY_MS);
  let year = startDate.getUTCFullYear();
  let month = startDate.getUTCMonth();
  while (year < endDate.getUTCFullYear() || (year === endDate.getUTCFullYear() && month <= endDate.getUTCMonth())) {
    const monthStart = Math.round(Date.UTC(year, month, 1) / DAY_MS);
    const daysInMonth = new Date(Date.UTC(year, month + 1, 0)).getUTCDate();
    const monthEnd = monthStart + daysInMonth - 1;
    const overlapStart = Math.max(start, monthStart);
    const overlapEnd = Math.min(end, monthEnd);
    if (overlapEnd >= overlapStart) {
      total += monthlyAdvance * (daysBetween(overlapStart, overlapEnd) / daysInMonth);
    }
    month += 1;
    if (month > 11) {
      month = 0;
      year += 1;
    }
  }
  return roundCurrency(total);
}

function buildSegments(
  period: OperatingCostPeriod,
  units: Unit[],
  contracts: Contract[],
  tenantsById: Map<string, Tenant>,
) {
  const periodStart = toDay(period.period_start);
  const periodEnd = toDay(period.period_end);
  const segments: Segment[] = [];

  const vacancy = (unit: Unit, start: number, end: number): Segment => ({
    lineKey: `vacancy:${unit.id}`,
    lineType: "vacancy",
    contract: null,
    tenant: null,
    unit,
    occupiedDays: daysBetween(start, end),
    areaSqm: unit.area_sqm ?? 0,
    advancePaid: 0,
  });

  for (const unit of units) {
    const unitContracts = contracts
      .filter((contract) => contract.unit_id === unit.id)
      .sort(
        (left, right) =>
          Math.max(toDay(left.start_date), periodStart) - Math.max(toDay(right.start_date), periodStart),
      );
    let cursor = periodStart;
    for (const contract of unitContracts) {
      const effectiveStart = Math.max(toDay(contract.start_date), periodStart, cursor);
      const effectiveEnd = Math.min(contract.end_date ? toDay(contract.end_date) : periodEnd, periodEnd);
      if (effectiveEnd < effectiveStart) {
        continue;
      }
      if (effectiveStart > cursor) {
        segments.push(vacancy(unit, cursor, effectiveStart - 1));
      }
      segments.push({
        lineKey: `contract:${contract.id}`,
        lineType: "contract",
        contract,
        tenant: tenantsById.get(contract.tenant_id) ?? null,
        unit,
        occupiedDays: daysBetween(effectiveStart, effectiveEnd),
        areaSqm: unit.area_sqm ?? 0,
        advancePaid: proratedAdvance(contract.service_charge_advance, effectiveStart, effectiveEnd),
      });
      cursor = effectiveEnd + 1;
      if (cursor > periodEnd) {
        break;
      }
    }
    if (cursor <= periodEnd) {
      segments.push(vacancy(unit, cursor, periodEnd));
    }
  }
  return segments.filter((segment) => segment.occupiedDays > 0);
}

function distributeAmount(amount: number, weights: Array<[string, number]>, denominator: number) {
  const totalCents = Math.round(amount * 100);
  let distributed = 0;
  const allocations = weights.map(([lineKey, weight]) => {
    const raw = (totalCents * weight) / denominator;
    const cents = Math.floor(raw);
    distributed += cents;
    return { lineKey, cents, fraction: raw - cents };
  });
  const remainder = totalCents - distributed;
  allocations.sort((left, right) => right.fraction - left.fraction);
  for (let index = 0; index < remainder; index += 1) {
    allocations[index % allocations.length].cents += 1;
  }
  const result = new Map<string, number>();
  for (const allocation of allocations) {
    result.set(allocation.lineKey, (result.get(allocation.lineKey) ?? 0) + allocation.cents);
  }
  return result;
}

function allocateItem(item: OperatingCostItem, units: Unit[], segments: Segment[], period: OperatingCostPeriod) {
  const periodDays = daysBetween(toDay(period.period_start), toDay(period.period_end));
  const totalUnits = Math.max(units.length, 1);
  const totalArea = units.reduce((sum, unit) => sum + (unit.area_sqm ?? 0), 0);
  const occupied = segments.filter((segment) => segment.contract !== null);
  const occupiedDaysTotal = occupied.reduce((sum, segment) => sum + segment.occupiedDays, 0);
  const advanceTotal = occupied.reduce(
    (sum, segment) => sum + (segment.advancePaid > 0 ? segment.advancePaid : 0),
    0,
  );

  let denominator: number;
  let weights: Array<[string, number]>;
  if (item.allocation_method === "unit_count") {
    denominator = totalUnits * periodDays;
    weights = segments.map((segment) => [segment.lineKey, segment.occupiedDays]);
  } else if (item.allocation_method === "occupancy_days") {
    denominator = occupiedDaysTotal;
    weights = occupied.map((segment) => [segment.lineKey, segment.occupiedDays]);
  } else if (item.allocation_method === "advance_share" && advanceTotal > 0) {
    denominator = advanceTotal;
    weights = occupied
      .filter((segment) => segment.advancePaid > 0)
      .map((segment) => [segment.lineKey, segment.advancePaid]);
  } else if (item.allocation_method === "advance_share") {
    denominator = occupiedDaysTotal;
    weights = occupied.map((segment) => [segment.lineKey, segment.occupiedDays]);
  } else if (totalArea > 0) {
    denominator = totalArea * periodDays;
    weights = segments.map((segment) => [segment.lineKey, segment.areaSqm * segment.occupiedDays]);
  } else {
    denominator = totalUnits * periodDays;
    weights = segments.map((segment) => [segment.lineKey, segment.occupiedDays]);
  }

  const filtered = weights.filter(([, weight]) => weight > 0);
  if (!filtered.length || denominator <= 0) {
    return new Map<string, number>();
  }
  return distributeAmount(item.amount, filtered, denominator);
}

/**
 * Nachbildung der Backend-Abrechnungslogik (Umlage nach Fläche, Einheiten, Belegungstagen
 * oder Vorauszahlungsanteil inkl. Leerstand), damit die Vorschau realistische Summen zeigt.
 */
export function buildSettlementPreview(
  period: OperatingCostPeriod,
  items: OperatingCostItem[],
  allUnits: Unit[],
  allContracts: Contract[],
  tenants: Tenant[],
): OperatingCostSettlementPreview {
  const units = allUnits.filter((unit) => unit.property_id === period.property_id);
  const unitIds = new Set(units.map((unit) => unit.id));
  const periodStart = toDay(period.period_start);
  const periodEnd = toDay(period.period_end);
  const contracts = allContracts.filter(
    (contract) =>
      unitIds.has(contract.unit_id) &&
      toDay(contract.start_date) <= periodEnd &&
      (!contract.end_date || toDay(contract.end_date) >= periodStart),
  );
  const segments = buildSegments(
    period,
    units,
    contracts,
    new Map(tenants.map((tenant) => [tenant.id, tenant])),
  );
  const billableItems = items.filter((item) => item.billable);
  const totalBillable = roundCurrency(billableItems.reduce((sum, item) => sum + item.amount, 0));
  const totalAdvance = roundCurrency(
    segments.filter((segment) => segment.contract).reduce((sum, segment) => sum + segment.advancePaid, 0),
  );

  if (!segments.length) {
    return { period, items, total_billable_amount: totalBillable, total_advance_amount: 0, lines: [] };
  }

  const shareCents = new Map<string, number>();
  const firstSegment = new Map<string, Segment>();
  const occupiedDays = new Map<string, number>();
  const advance = new Map<string, number>();
  for (const segment of segments) {
    shareCents.set(segment.lineKey, 0);
    if (!firstSegment.has(segment.lineKey)) {
      firstSegment.set(segment.lineKey, segment);
    }
    occupiedDays.set(segment.lineKey, (occupiedDays.get(segment.lineKey) ?? 0) + segment.occupiedDays);
    advance.set(segment.lineKey, (advance.get(segment.lineKey) ?? 0) + segment.advancePaid);
  }
  for (const item of billableItems) {
    for (const [lineKey, cents] of allocateItem(item, units, segments, period)) {
      shareCents.set(lineKey, (shareCents.get(lineKey) ?? 0) + cents);
    }
  }

  const lines: OperatingCostSettlementLine[] = [];
  for (const [lineKey, segment] of firstSegment) {
    const share = (shareCents.get(lineKey) ?? 0) / 100;
    const advancePaid = roundCurrency(advance.get(lineKey) ?? 0);
    lines.push({
      line_type: segment.lineType,
      contract_id: segment.contract?.id ?? null,
      tenant_id: segment.contract?.tenant_id ?? null,
      tenant_name: segment.tenant
        ? `${segment.tenant.first_name} ${segment.tenant.last_name}`.trim()
        : "Leerstand",
      unit_id: segment.unit.id,
      unit_name: segment.unit.name,
      allocation_factor: totalBillable > 0 ? Math.round((share / totalBillable) * 10000) / 10000 : 0,
      occupied_days: occupiedDays.get(lineKey) ?? segment.occupiedDays,
      share_amount: roundCurrency(share),
      advance_paid_amount: advancePaid,
      balance_amount: roundCurrency(share - advancePaid),
    });
  }
  lines.sort(
    (left, right) =>
      left.unit_name.toLowerCase().localeCompare(right.unit_name.toLowerCase()) ||
      left.line_type.localeCompare(right.line_type) ||
      (left.tenant_name ?? "").toLowerCase().localeCompare((right.tenant_name ?? "").toLowerCase()),
  );

  return {
    period,
    items,
    total_billable_amount: totalBillable,
    total_advance_amount: totalAdvance,
    lines,
  };
}
