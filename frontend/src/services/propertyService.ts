import { apiClient } from "./apiClient";

export type Property = {
  id: string;
  organization_id: string;
  name: string;
  property_type: string;
  street?: string | null;
  city?: string | null;
  postal_code?: string | null;
  purchase_price?: number | null;
};

export async function listProperties() {
  const response = await apiClient.get<Property[]>("/properties/");
  return response.data;
}
