import { apiClient } from "./apiClient";

export type Invoice = {
  id: string;
  organization_id: string;
  property_id?: string | null;
  vendor_name: string;
  invoice_number?: string | null;
  invoice_date?: string | null;
  gross_amount: number;
  status: string;
};

export type CreateInvoicePayload = {
  property_id?: string | null;
  vendor_name: string;
  invoice_number?: string | null;
  invoice_date?: string | null;
  gross_amount: number;
  status: string;
};

export async function listInvoices() {
  const response = await apiClient.get<Invoice[]>("/invoices/");
  return response.data;
}

export async function createInvoice(payload: CreateInvoicePayload) {
  const response = await apiClient.post<Invoice>("/invoices/", payload);
  return response.data;
}
