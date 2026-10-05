import { apiClient } from "./apiClient";

export type Organization = {
  id: string;
  name: string;
  legal_name?: string | null;
  street?: string | null;
  postal_code?: string | null;
  city?: string | null;
  country: string;
  contact_email?: string | null;
  contact_phone?: string | null;
};

export type UpdateOrganizationPayload = {
  name: string;
  legal_name?: string | null;
  street?: string | null;
  postal_code?: string | null;
  city?: string | null;
  country: string;
  contact_email?: string | null;
  contact_phone?: string | null;
};

export async function getCurrentOrganization() {
  const response = await apiClient.get<Organization>("/organization/me");
  return response.data;
}

export async function updateCurrentOrganization(payload: UpdateOrganizationPayload) {
  const response = await apiClient.put<Organization>("/organization/me", payload);
  return response.data;
}
