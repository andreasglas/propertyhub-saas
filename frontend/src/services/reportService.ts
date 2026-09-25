import { apiClient } from "./apiClient";

export type DashboardReport = {
  properties_count: number;
  units_count: number;
  tenants_count: number;
  contracts_count: number;
  invoices_count: number;
  open_invoices_count: number;
  payments_count: number;
  accounting_entries_count: number;
  total_invoice_amount: number;
  total_payment_amount: number;
  total_income_amount: number;
  total_expense_amount: number;
};

export async function getDashboardReport() {
  const response = await apiClient.get<DashboardReport>("/reports/");
  return response.data;
}
