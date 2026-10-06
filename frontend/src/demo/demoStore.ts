import { DEMO_DATA_VERSION, DEMO_STORAGE_KEYS, resetDemoData } from "./demoConfig";
import { createDemoSeed, DemoState } from "./demoSeed";

let cachedState: DemoState | null = null;

function getStorage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function isValidState(value: unknown): value is DemoState {
  if (!value || typeof value !== "object") {
    return false;
  }
  const candidate = value as Partial<DemoState>;
  return (
    candidate.version === DEMO_DATA_VERSION &&
    Array.isArray(candidate.properties) &&
    Array.isArray(candidate.users) &&
    Array.isArray(candidate.tasks) &&
    typeof candidate.organization === "object"
  );
}

/** Lädt den versionierten Demo-Bestand aus dem Browser oder erzeugt frische Beispieldaten. */
export function getDemoState(): DemoState {
  if (cachedState) {
    return cachedState;
  }
  const storage = getStorage();
  try {
    const raw = storage?.getItem(DEMO_STORAGE_KEYS.data);
    const parsed: unknown = raw ? JSON.parse(raw) : null;
    if (isValidState(parsed)) {
      cachedState = parsed;
      return cachedState;
    }
  } catch {
    // Beschädigte oder veraltete Demo-Daten werden durch einen frischen Seed ersetzt.
  }
  cachedState = createDemoSeed();
  saveDemoState(cachedState);
  return cachedState;
}

export function saveDemoState(state: DemoState) {
  cachedState = state;
  try {
    getStorage()?.setItem(DEMO_STORAGE_KEYS.data, JSON.stringify(state));
  } catch {
    // Ohne Speicher (z. B. volles Kontingent) bleibt der Stand nur bis zum Neuladen erhalten.
  }
}

/** Setzt die Demo-Daten auf den Ausgangszustand zurück (Speicher und In-Memory-Cache). */
export function resetDemoStore() {
  cachedState = null;
  resetDemoData();
}
