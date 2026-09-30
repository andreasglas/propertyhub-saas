import { apiClient } from "./apiClient";

export type OperatingCostPeriod = {
  id: string;
  organization_id: string;
  property_id: string;
  name: string;
  period_start: string;
  period_end: string;
  status: string;
};

export type OperatingCostItem = {
  id: string;
  organization_id: string;
  period_id: string;
  category: string;
  description?: string | null;
  allocation_method: string;
  amount: number;
  billable: boolean;
};

export type OperatingCostSettlementLine = {
  line_type: string;
  contract_id?: string | null;
  tenant_id?: string | null;
  tenant_name?: string | null;
  unit_id: string;
  unit_name: string;
  allocation_factor: number;
  occupied_days: number;
  share_amount: number;
  advance_paid_amount: number;
  balance_amount: number;
};

export type OperatingCostSettlementPreview = {
  period: OperatingCostPeriod;
  items: OperatingCostItem[];
  total_billable_amount: number;
  total_advance_amount: number;
  lines: OperatingCostSettlementLine[];
};

export async function listOperatingCostPeriods() {
  const response = await apiClient.get<OperatingCostPeriod[]>("/operating-costs/periods");
  return response.data;
}

export async function createOperatingCostPeriod(payload: {
  property_id: string;
  name: string;
  period_start: string;
  period_end: string;
  status: string;
}) {
  const response = await apiClient.post<OperatingCostPeriod>("/operating-costs/periods", payload);
  return response.data;
}

export async function listOperatingCostItems(periodId: string) {
  const response = await apiClient.get<OperatingCostItem[]>(
    `/operating-costs/periods/${periodId}/items`,
  );
  return response.data;
}

export async function createOperatingCostItem(
  periodId: string,
  payload: {
    category: string;
    description?: string | null;
    allocation_method: string;
    amount: number;
    billable: boolean;
  },
) {
  const response = await apiClient.post<OperatingCostItem>(
    `/operating-costs/periods/${periodId}/items`,
    payload,
  );
  return response.data;
}

export async function getOperatingCostSettlementPreview(periodId: string) {
  const response = await apiClient.get<OperatingCostSettlementPreview>(
    `/operating-costs/periods/${periodId}/settlement-preview`,
  );
  return response.data;
}

export async function finalizeOperatingCostPeriod(periodId: string) {
  const response = await apiClient.post<OperatingCostPeriod>(
    `/operating-costs/periods/${periodId}/finalize`,
  );
  return response.data;
}

export async function downloadOperatingCostSettlementCsv(periodId: string) {
  const response = await apiClient.get<Blob>(`/operating-costs/periods/${periodId}/export.csv`, {
    responseType: "blob",
  });
  return response.data;
}

export async function downloadOperatingCostSettlementPdf(periodId: string) {
  const response = await apiClient.get<Blob>(`/operating-costs/periods/${periodId}/export.pdf`, {
    responseType: "blob",
  });
  return response.data;
}
