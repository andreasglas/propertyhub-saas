/**
 * Demo-Modus: wird ausschließlich über das Build-Flag `VITE_DEMO_MODE=true` aktiviert.
 * Ohne dieses Flag bleibt der normale Backendbetrieb (echte Authentifizierung) unverändert.
 */
export function isDemoModeEnabled() {
  return import.meta.env.VITE_DEMO_MODE === "true";
}

export const DEMO_DATA_VERSION = 1;

// Eigene Schlüssel, getrennt von `propertyhub.auth.token` des normalen Betriebs.
export const DEMO_STORAGE_KEYS = {
  dataPrefix: "propertyhub.demo.data.v",
  data: `propertyhub.demo.data.v${DEMO_DATA_VERSION}`,
  session: "propertyhub.demo.auth.session",
} as const;

export const DEMO_PASSWORD = "demo1234";

// Öffentlich dokumentierte, ausschließlich fiktive Demo-Zugänge.
export const DEMO_ACCOUNTS = [
  { email: "demo@propertyhub.example", role: "owner", label: "Owner – Vollzugriff" },
  { email: "manager@propertyhub.example", role: "manager", label: "Manager" },
  { email: "viewer@propertyhub.example", role: "viewer", label: "Viewer – nur lesen" },
] as const;

export const DEMO_PRIMARY_ACCOUNT = DEMO_ACCOUNTS[0];

function getStorage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

/** Entfernt alle gespeicherten Demo-Daten (auch ältere Versionen). Die Demo-Sitzung bleibt erhalten. */
export function resetDemoData() {
  const storage = getStorage();
  if (!storage) {
    return;
  }
  const keys: string[] = [];
  for (let index = 0; index < storage.length; index += 1) {
    const key = storage.key(index);
    if (key?.startsWith(DEMO_STORAGE_KEYS.dataPrefix)) {
      keys.push(key);
    }
  }
  keys.forEach((key) => storage.removeItem(key));
}
