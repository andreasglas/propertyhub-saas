import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// Eigene Test-Konfiguration ohne PWA-Plugin; Tests laufen in jsdom ohne Backend.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
    restoreMocks: true,
    unstubEnvs: true,
    testTimeout: 20000,
  },
});
