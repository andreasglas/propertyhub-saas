import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { PropsWithChildren } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.hoisted(() => {
  // Muss vor dem Import von apiClient/AuthContext gesetzt sein (Flag wird beim Laden ausgewertet).
  (import.meta.env as Record<string, string>).VITE_DEMO_MODE = "true";
});

import { AuthProvider, useAuth } from "../../context/AuthContext";
import { DEMO_PASSWORD, DEMO_PRIMARY_ACCOUNT, DEMO_STORAGE_KEYS } from "../demoConfig";
import { blockNetwork } from "./networkGuard";

const wrapper = ({ children }: PropsWithChildren) => <AuthProvider>{children}</AuthProvider>;

let networkAttempts: string[] = [];

beforeEach(() => {
  networkAttempts = blockNetwork();
});

async function loginError(login: (email: string, password: string) => Promise<void>, email: string, password: string) {
  let error: unknown = null;
  await act(async () => {
    try {
      await login(email, password);
    } catch (caught) {
      error = caught;
    }
  });
  return error;
}

afterEach(() => {
  cleanup();
  expect(networkAttempts).toEqual([]);
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

describe("Demo-Login, Logout und Sitzungswiederherstellung", () => {
  it("lehnt falsche Zugangsdaten ab", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(await loginError(result.current.login, DEMO_PRIMARY_ACCOUNT.email, "falsches-passwort")).toBeTruthy();
    expect(await loginError(result.current.login, "unbekannt@example.com", DEMO_PASSWORD)).toBeTruthy();
    expect(result.current.isAuthenticated).toBe(false);
    expect(window.localStorage.getItem(DEMO_STORAGE_KEYS.session)).toBeNull();
  });

  it("meldet mit Demo-Zugangsdaten an, stellt die Sitzung nach Reload wieder her und meldet ab", async () => {
    const first = renderHook(() => useAuth(), { wrapper });

    await act(() => first.result.current.login(DEMO_PRIMARY_ACCOUNT.email, DEMO_PASSWORD));
    await waitFor(() => expect(first.result.current.currentUser?.email).toBe(DEMO_PRIMARY_ACCOUNT.email));
    expect(first.result.current.currentUser?.role).toBe("owner");

    const storedToken = window.localStorage.getItem(DEMO_STORAGE_KEYS.session);
    expect(storedToken).toMatch(/^demo\./);
    expect(window.localStorage.getItem("propertyhub.auth.token")).toBeNull();
    first.unmount();

    // Simulierter Seiten-Reload: neuer Provider liest die gespeicherte Demo-Sitzung.
    const second = renderHook(() => useAuth(), { wrapper });
    expect(second.result.current.isAuthenticated).toBe(true);
    await waitFor(() => expect(second.result.current.currentUser?.email).toBe(DEMO_PRIMARY_ACCOUNT.email));

    act(() => second.result.current.logout());
    expect(second.result.current.isAuthenticated).toBe(false);
    expect(window.localStorage.getItem(DEMO_STORAGE_KEYS.session)).toBeNull();
  });

  it("verwirft ungültige gespeicherte Demo-Sitzungen", async () => {
    window.localStorage.setItem(DEMO_STORAGE_KEYS.session, "kein-gueltiges-token");
    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.isAuthenticated).toBe(false));
    expect(window.localStorage.getItem(DEMO_STORAGE_KEYS.session)).toBeNull();
  });

  it("verwendet kein echtes Backend-Token als Demo-Sitzung", async () => {
    window.localStorage.setItem("propertyhub.auth.token", "echtes-token");
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(false);
    expect(window.localStorage.getItem("propertyhub.auth.token")).toBe("echtes-token");
  });
});
