import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig(({ command, isPreview }) => ({
  base: command === "build" || isPreview ? "/propertyhub-saas/" : "/",
  plugins: [
    react(),
    VitePWA({
      registerType: "prompt",
      base: "/propertyhub-saas/",
      scope: "/propertyhub-saas/",
      manifest: {
        name: "PropertyHub",
        short_name: "PropertyHub",
        lang: "de",
        start_url: "/propertyhub-saas/",
        scope: "/propertyhub-saas/",
        display: "standalone",
        theme_color: "#1976d2",
        background_color: "#ffffff",
        icons: [
          { src: "icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "icon-512.png", sizes: "512x512", type: "image/png" },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,png,webmanifest}"],
        globIgnores: ["**/404.html"],
        navigateFallbackDenylist: [/^\/api(?:\/|$)/],
      },
    }),
  ],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_PROXY_TARGET ?? "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
}));
