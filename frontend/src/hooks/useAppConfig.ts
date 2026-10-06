import { isDemoModeEnabled } from "../demo/demoConfig";

export function useAppConfig() {
  return {
    appName: "PropertyHub",
    isDemoMode: isDemoModeEnabled(),
    apiBaseUrl:
      import.meta.env.VITE_API_BASE_URL?.toString() ?? "http://localhost:8000",
  };
}
