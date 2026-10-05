import { apiClient } from "./apiClient";

export type BankTransaction = {
  id: string;
  organization_id: string;
  payment_id?: string | null;
  external_id?: string | null;
  account_name: string;
  transaction_type: string;
  booking_date?: string | null;
  value_date?: string | null;
  amount: number;
  currency: string;
  counterparty_name?: string | null;
  iban?: string | null;
  reference?: string | null;
  status: string;
};

type BankImportResult = {
  imported_count: number;
  transactions: BankTransaction[];
};

export async function listBankTransactions() {
  const response = await apiClient.get<BankTransaction[]>("/banking/");
  return response.data;
}

export async function importBankTransactions() {
  const response = await apiClient.post<BankImportResult>("/banking/import-stub");
  return response.data;
}

export async function matchBankTransaction(transactionId: string, payment_id: string) {
  const response = await apiClient.post<BankTransaction>(
    `/banking/transactions/${transactionId}/match-payment`,
    { payment_id },
  );
  return response.data;
}
