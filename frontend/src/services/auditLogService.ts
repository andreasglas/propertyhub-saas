import { apiClient } from "./apiClient";

export type AuditLogEntry = {
  id: string;
  organization_id: string;
  actor_user_id?: string | null;
  actor_email?: string | null;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  summary: string;
  details?: Record<string, string | number | boolean | null> | null;
  created_at: string;
};

export async function listAuditLogs(params?: {
  action?: string;
  resource_type?: string;
  limit?: number;
}) {
  const response = await apiClient.get<AuditLogEntry[]>("/audit-logs/", { params });
  return response.data;
}
