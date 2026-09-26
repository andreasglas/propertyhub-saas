import { apiClient } from "./apiClient";

export type ManagedUser = {
  id: string;
  organization_id: string;
  email: string;
  full_name?: string | null;
  role: string;
  is_active: boolean;
  invitation_sent_at?: string | null;
  invitation_accepted_at?: string | null;
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

export type InviteUserPayload = {
  email: string;
  full_name?: string | null;
  role: string;
};

export type UserInvitationResult = {
  user: ManagedUser;
  invitation_token: string;
  setup_path: string;
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

export async function inviteUser(payload: InviteUserPayload) {
  const response = await apiClient.post<UserInvitationResult>("/users/invitations", payload);
  return response.data;
}

export async function resendUserInvitation(userId: string) {
  const response = await apiClient.post<UserInvitationResult>(`/users/${userId}/invite`);
  return response.data;
}
