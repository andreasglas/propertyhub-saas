import { apiClient } from "./apiClient";

export type Vendor = {
  id: string;
  organization_id: string;
  name: string;
  service_type: string;
  contact_email?: string | null;
  contact_phone?: string | null;
  notes?: string | null;
};

export type VendorPayload = {
  name: string;
  service_type: string;
  contact_email?: string | null;
  contact_phone?: string | null;
  notes?: string | null;
};

export async function listVendors() {
  const response = await apiClient.get<Vendor[]>("/vendors/");
  return response.data;
}

export async function createVendor(payload: VendorPayload) {
  const response = await apiClient.post<Vendor>("/vendors/", payload);
  return response.data;
}
