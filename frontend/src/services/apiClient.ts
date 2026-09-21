import axios from "axios";

const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL?.toString() ?? "/api";

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    "Content-Type": "application/json",
  },
});
