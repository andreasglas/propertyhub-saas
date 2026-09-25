import { apiClient } from "./apiClient";

type TokenResponse = {
  access_token: string;
  token_type: string;
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
