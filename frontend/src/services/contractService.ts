import { apiClient } from "./apiClient";

export type Contract = {
  id: string;
  organization_id: string;
  unit_id: string;
  tenant_id: string;
  start_date: string;
  end_date?: string | null;
  cold_rent: number;
  service_charge_advance: number;
};

export type CreateContractPayload = {
  unit_id: string;
  tenant_id: string;
  start_date: string;
  end_date?: string | null;
  cold_rent: number;
  service_charge_advance: number;
};

export async function listContracts() {
  const response = await apiClient.get<Contract[]>("/contracts/");
  return response.data;
}

export async function createContract(payload: CreateContractPayload) {
  const response = await apiClient.post<Contract>("/contracts/", payload);
  return response.data;
}
