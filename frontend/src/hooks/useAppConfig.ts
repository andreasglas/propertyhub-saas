export function useAppConfig() {
  return {
    appName: "PropertyHub",
    apiBaseUrl:
      import.meta.env.VITE_API_BASE_URL?.toString() ?? "http://localhost:8000",
  };
}
