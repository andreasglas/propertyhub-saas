import axios from "axios";

const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL?.toString() ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    "Content-Type": "application/json",
  },
});
