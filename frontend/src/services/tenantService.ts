import { apiClient } from "./apiClient";

export type Tenant = {
  id: string;
  organization_id: string;
  first_name: string;
  last_name: string;
  email?: string | null;
  phone?: string | null;
  move_in_date?: string | null;
  move_out_date?: string | null;
};

export type CreateTenantPayload = {
  first_name: string;
  last_name: string;
  email?: string | null;
  phone?: string | null;
  move_in_date?: string | null;
  move_out_date?: string | null;
};

export async function listTenants() {
  const response = await apiClient.get<Tenant[]>("/tenants/");
  return response.data;
}

export async function createTenant(payload: CreateTenantPayload) {
  const response = await apiClient.post<Tenant>("/tenants/", payload);
  return response.data;
}
