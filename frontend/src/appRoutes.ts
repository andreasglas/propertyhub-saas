export type AppRoute =
  | "overview"
  | "setup-password"
  | "activity"
  | "organization"
  | "users"
  | "properties"
  | "units"
  | "tenants"
  | "contracts"
  | "operating-costs"
  | "accounting"
  | "billing"
  | "banking"
  | "documents";

export const appRoutePaths: Record<AppRoute, string> = {
  overview: "/",
  "setup-password": "/setup-password",
  activity: "/activity",
  organization: "/organization",
  users: "/users",
  properties: "/properties",
  units: "/units",
  tenants: "/tenants",
  contracts: "/contracts",
  "operating-costs": "/operating-costs",
  accounting: "/accounting",
  billing: "/billing",
  banking: "/banking",
  documents: "/documents",
};

export function getRouteFromPath(pathname: string): AppRoute {
  const entry = Object.entries(appRoutePaths).find(([, path]) => path === pathname);
  return (entry?.[0] as AppRoute | undefined) ?? "overview";
}
