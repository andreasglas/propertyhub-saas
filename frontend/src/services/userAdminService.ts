import { apiClient } from "./apiClient";

export type ManagedUser = {
  id: string;
  organization_id: string;
  email: string;
  full_name?: string | null;
  role: string;
  is_active: boolean;
};

export type CreateManagedUserPayload = {
  email: string;
  full_name?: string | null;
  password: string;
  role: string;
  is_active: boolean;
};

export type UpdateManagedUserPayload = {
  full_name?: string | null;
  password?: string | null;
  role: string;
  is_active: boolean;
};

export async function listUsers() {
  const response = await apiClient.get<ManagedUser[]>("/users/");
  return response.data;
}

export async function createUser(payload: CreateManagedUserPayload) {
  const response = await apiClient.post<ManagedUser>("/users/", payload);
  return response.data;
}

export async function updateUser(userId: string, payload: UpdateManagedUserPayload) {
  const response = await apiClient.put<ManagedUser>(`/users/${userId}`, payload);
  return response.data;
}
