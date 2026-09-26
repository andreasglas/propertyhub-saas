import { useEffect, useState } from "react";

import { AppRoute, appRoutePaths, getRouteFromPath } from "./appRoutes";
import { AppShell } from "./components/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { SetupPasswordPage } from "./pages/SetupPasswordPage";

export function App() {
  const [currentRoute, setCurrentRoute] = useState<AppRoute>(() =>
    getRouteFromPath(window.location.pathname),
  );

  useEffect(() => {
    const handlePopState = () => {
      setCurrentRoute(getRouteFromPath(window.location.pathname));
    };

    window.addEventListener("popstate", handlePopState);
    return () => {
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);

  function navigate(route: AppRoute) {
    const nextPath = appRoutePaths[route];
    if (window.location.pathname !== nextPath) {
      window.history.pushState({}, "", nextPath);
    }
    setCurrentRoute(route);
  }

  return (
    <AppShell currentRoute={currentRoute} onNavigate={navigate}>
      {currentRoute === "setup-password" ? (
        <SetupPasswordPage />
      ) : (
        <DashboardPage currentRoute={currentRoute} />
      )}
    </AppShell>
  );
}
