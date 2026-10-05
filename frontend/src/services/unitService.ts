import { apiClient } from "./apiClient";

export type Unit = {
  id: string;
  organization_id: string;
  property_id: string;
  name: string;
  unit_type: string;
  status: string;
  area_sqm?: number | null;
};

export type CreateUnitPayload = {
  property_id: string;
  name: string;
  unit_type: string;
  status: string;
  area_sqm?: number | null;
};

export async function listUnits() {
  const response = await apiClient.get<Unit[]>("/units/");
  return response.data;
}

export async function createUnit(payload: CreateUnitPayload) {
  const response = await apiClient.post<Unit>("/units/", payload);
  return response.data;
}
