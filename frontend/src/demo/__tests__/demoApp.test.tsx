import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.hoisted(() => {
  // Muss vor dem Import von apiClient/AuthContext gesetzt sein (Flag wird beim Laden ausgewertet).
  (import.meta.env as Record<string, string>).VITE_DEMO_MODE = "true";
});

import { App } from "../../App";
import { appRoutePaths, AppRoute } from "../../appRoutes";
import { AuthProvider } from "../../context/AuthContext";
import { resetDemoStore } from "../demoStore";
import { blockNetwork } from "./networkGuard";

let networkAttempts: string[] = [];

beforeEach(() => {
  window.localStorage.clear();
  resetDemoStore();
  window.history.replaceState({}, "", "/");
  networkAttempts = blockNetwork();
});

afterEach(() => {
  cleanup();
  expect(networkAttempts).toEqual([]);
  vi.unstubAllGlobals();
});

function errorAlerts() {
  // Fehlgeschlagene OCR-Beispieldokumente sind gewollte Statusvarianten und keine API-Fehler.
  return Array.from(document.querySelectorAll(".MuiAlert-colorError"))
    .map((element) => element.textContent ?? "")
    .filter((text) => !text.startsWith("OCR fehlgeschlagen: "));
}

describe("Demo-App ohne Backend", () => {
  it("zeigt Demo-Hinweis und Zugangsdaten, meldet an und zeigt alle Bereiche mit Beispieldaten", async () => {
    render(
      <AuthProvider>
        <App />
      </AuthProvider>,
    );

    expect(screen.getByTestId("demo-banner")).toBeTruthy();
    expect(screen.getByTestId("demo-credentials").textContent).toContain("demo@propertyhub.example");

    fireEvent.click(screen.getByRole("button", { name: "Login" }));
    await waitFor(() => expect(screen.queryByRole("button", { name: "Login" })).toBeNull(), { timeout: 5000 });
    await waitFor(() => expect(document.body.textContent).toContain("Dana Demo"), { timeout: 5000 });
    expect(errorAlerts()).toEqual([]);

    const routes = Object.keys(appRoutePaths).filter((route) => route !== "setup-password") as AppRoute[];
    for (const route of routes) {
      await act(async () => {
        window.history.pushState({}, "", appRoutePaths[route]);
        window.dispatchEvent(new PopStateEvent("popstate"));
      });
      await waitFor(() => expect(document.body.textContent).not.toMatch(/wird geladen/i));
      expect(errorAlerts(), `Bereich ${route}`).toEqual([]);
      expect(document.body.textContent, `Bereich ${route}`).not.toContain("Demo-Modus nicht verfügbar");
      if (route === "properties") {
        expect(document.body.textContent).toContain("Lindenhof 12");
      }
    }
  });
});
