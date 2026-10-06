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
  | "tasks"
  | "operating-costs"
  | "accounting"
  | "billing"
  | "banking"
  | "documents";

const routePaths: Record<AppRoute, string> = {
  overview: "/",
  "setup-password": "/setup-password",
  activity: "/activity",
  organization: "/organization",
  users: "/users",
  properties: "/properties",
  units: "/units",
  tenants: "/tenants",
  contracts: "/contracts",
  tasks: "/tasks",
  "operating-costs": "/operating-costs",
  accounting: "/accounting",
  billing: "/billing",
  banking: "/banking",
  documents: "/documents",
};

export const appRoutePaths = Object.fromEntries(
  Object.entries(routePaths).map(([route, path]) => [
    route,
    import.meta.env.BASE_URL + path.slice(1),
  ]),
) as Record<AppRoute, string>;

export function getRouteFromPath(pathname: string): AppRoute {
  const entry = Object.entries(appRoutePaths).find(([, path]) => path === pathname);
  return (entry?.[0] as AppRoute | undefined) ?? "overview";
}
