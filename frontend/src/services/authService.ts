import { apiClient } from "./apiClient";

type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type AuthUser = {
  id: string;
  organization_id: string;
  email: string;
  full_name?: string | null;
  role: string;
  is_active: boolean;
};

export async function login(email: string, password: string) {
  const payload = new URLSearchParams();
  payload.set("username", email);
  payload.set("password", password);

  const response = await apiClient.post<TokenResponse>("/auth/token", payload, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  return response.data;
}

export async function getCurrentUser() {
  const response = await apiClient.get<AuthUser>("/auth/me");
  return response.data;
}
