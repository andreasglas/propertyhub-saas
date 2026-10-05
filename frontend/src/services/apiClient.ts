import axios from "axios";

const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL?.toString() || "/api";

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

export function setAuthToken(token: string | null) {
  if (token) {
    apiClient.defaults.headers.common.Authorization = "Bearer " + token;
    return;
  }

  delete apiClient.defaults.headers.common.Authorization;
}
