export type AppRoute =
  | "overview"
  | "setup-password"
  | "organization"
  | "users"
  | "properties"
  | "units"
  | "tenants"
  | "contracts"
  | "accounting"
  | "billing"
  | "banking"
  | "documents";

export const appRoutePaths: Record<AppRoute, string> = {
  overview: "/",
  "setup-password": "/setup-password",
  organization: "/organization",
  users: "/users",
  properties: "/properties",
  units: "/units",
  tenants: "/tenants",
  contracts: "/contracts",
  accounting: "/accounting",
  billing: "/billing",
  banking: "/banking",
  documents: "/documents",
};

export function getRouteFromPath(pathname: string): AppRoute {
  const entry = Object.entries(appRoutePaths).find(([, path]) => path === pathname);
  return (entry?.[0] as AppRoute | undefined) ?? "overview";
}
