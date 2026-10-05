import { apiClient } from "./apiClient";

export type AccountingEntry = {
  id: string;
  organization_id: string;
  property_id?: string | null;
  entry_type: string;
  category?: string | null;
  amount: number;
  booking_date?: string | null;
};

export type CreateAccountingEntryPayload = {
  property_id?: string | null;
  entry_type: string;
  category?: string | null;
  amount: number;
  booking_date?: string | null;
};

export async function listAccountingEntries() {
  const response = await apiClient.get<AccountingEntry[]>("/accounting/");
  return response.data;
}

export async function createAccountingEntry(
  payload: CreateAccountingEntryPayload,
) {
  const response = await apiClient.post<AccountingEntry>("/accounting/", payload);
  return response.data;
}
