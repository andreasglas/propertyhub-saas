export type AppRoute = "overview" | "accounting" | "billing" | "banking" | "documents";

export const appRoutePaths: Record<AppRoute, string> = {
  overview: "/",
  accounting: "/accounting",
  billing: "/billing",
  banking: "/banking",
  documents: "/documents",
};

export function getRouteFromPath(pathname: string): AppRoute {
  const entry = Object.entries(appRoutePaths).find(([, path]) => path === pathname);
  return (entry?.[0] as AppRoute | undefined) ?? "overview";
}
