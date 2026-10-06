import { afterEach, describe, expect, it, vi } from "vitest";

import { blockNetwork } from "./networkGuard";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.resetModules();
  window.localStorage.clear();
});

describe("Aktivierung des Demo-Modus", () => {
  it.each(["", "false", "1", "TRUE", "yes"])("bleibt bei VITE_DEMO_MODE=%j deaktiviert", async (value) => {
    vi.stubEnv("VITE_DEMO_MODE", value);
    const { isDemoModeEnabled } = await import("../demoConfig");
    const { apiClient } = await import("../../services/apiClient");

    expect(isDemoModeEnabled()).toBe(false);
    expect(typeof apiClient.defaults.adapter).not.toBe("function");
  });

  it("ersetzt bei VITE_DEMO_MODE=true den Netzwerkadapter des API-Clients", async () => {
    vi.stubEnv("VITE_DEMO_MODE", "true");
    const { isDemoModeEnabled } = await import("../demoConfig");
    const { apiClient } = await import("../../services/apiClient");

    expect(isDemoModeEnabled()).toBe(true);
    expect(typeof apiClient.defaults.adapter).toBe("function");
  });

  it("nutzt ohne Flag die echte Backend-Authentifizierung – Demo-Zugangsdaten werden nicht lokal akzeptiert", async () => {
    vi.stubEnv("VITE_DEMO_MODE", "false");
    const attempts = blockNetwork();
    const { login } = await import("../../services/authService");
    const { DEMO_PASSWORD, DEMO_PRIMARY_ACCOUNT } = await import("../demoConfig");

    await expect(login(DEMO_PRIMARY_ACCOUNT.email, DEMO_PASSWORD)).rejects.toThrow();
    expect(attempts).toEqual(["POST /api/auth/token"]);
    expect(window.localStorage.getItem("propertyhub.demo.data.v1")).toBeNull();
  });
});
