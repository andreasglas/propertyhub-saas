import axios from "axios";

import { isDemoModeEnabled } from "../demo/demoConfig";

const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL?.toString() || "/api";

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

if (isDemoModeEnabled()) {
  // Demo-Modus: alle Requests werden lokal beantwortet, es findet kein Netzwerkzugriff statt.
  // Der Demo-Code wird nur bei aktivem Flag nachgeladen und ist im normalen Build nicht enthalten.
  apiClient.defaults.adapter = async (config) => {
    const { demoAdapter } = await import("../demo/demoApi");
    return demoAdapter(config);
  };
}

export function setAuthToken(token: string | null) {
  if (token) {
    apiClient.defaults.headers.common.Authorization = "Bearer " + token;
    return;
  }

  delete apiClient.defaults.headers.common.Authorization;
}
