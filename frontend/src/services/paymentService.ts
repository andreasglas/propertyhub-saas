import { apiClient } from "./apiClient";

export type Payment = {
  id: string;
  organization_id: string;
  invoice_id?: string | null;
  contract_id?: string | null;
  amount: number;
  booking_date?: string | null;
  reference?: string | null;
};

export type CreatePaymentPayload = {
  invoice_id?: string | null;
  contract_id?: string | null;
  amount: number;
  booking_date?: string | null;
  reference?: string | null;
};

export async function listPayments() {
  const response = await apiClient.get<Payment[]>("/payments/");
  return response.data;
}

export async function createPayment(payload: CreatePaymentPayload) {
  const response = await apiClient.post<Payment>("/payments/", payload);
  return response.data;
}
