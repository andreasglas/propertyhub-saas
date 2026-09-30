import { apiClient } from "./apiClient";
import { DocumentRecord } from "./documentService";

export type TaskItem = {
  id: string;
  organization_id: string;
  property_id?: string | null;
  unit_id?: string | null;
  vendor_id?: string | null;
  recurring_template_id?: string | null;
  title: string;
  description?: string | null;
  category: string;
  priority: string;
  status: string;
  due_date?: string | null;
  estimated_cost?: number | null;
  actual_cost?: number | null;
  assignee_name?: string | null;
  completion_notes?: string | null;
  completed_at?: string | null;
  source: string;
};

export type TaskPayload = {
  property_id?: string | null;
  unit_id?: string | null;
  vendor_id?: string | null;
  recurring_template_id?: string | null;
  title: string;
  description?: string | null;
  category: string;
  priority: string;
  status: string;
  due_date?: string | null;
  estimated_cost?: number | null;
  actual_cost?: number | null;
  assignee_name?: string | null;
  completion_notes?: string | null;
  source: string;
};

export type TaskComment = {
  id: string;
  organization_id: string;
  task_id: string;
  author_user_id?: string | null;
  author_email?: string | null;
  message: string;
  created_at: string;
};

export type TaskHistoryEntry = {
  entry_type: string;
  entry_id: string;
  created_at: string;
  actor_email?: string | null;
  title: string;
  message: string;
  metadata?: Record<string, string | number | boolean | null | string[]> | null;
};

export type TaskTemplate = {
  id: string;
  organization_id: string;
  property_id?: string | null;
  unit_id?: string | null;
  vendor_id?: string | null;
  title: string;
  description?: string | null;
  category: string;
  priority: string;
  recurrence_frequency: string;
  next_due_date: string;
  assignee_name?: string | null;
  active: boolean;
};

export type TaskTemplatePayload = {
  property_id?: string | null;
  unit_id?: string | null;
  vendor_id?: string | null;
  title: string;
  description?: string | null;
  category: string;
  priority: string;
  recurrence_frequency: string;
  next_due_date: string;
  assignee_name?: string | null;
  active: boolean;
};

export async function listTasks() {
  const response = await apiClient.get<TaskItem[]>("/tasks/");
  return response.data;
}

export async function createTask(payload: TaskPayload) {
  const response = await apiClient.post<TaskItem>("/tasks/", payload);
  return response.data;
}

export async function updateTask(taskId: string, payload: TaskPayload) {
  const response = await apiClient.put<TaskItem>(`/tasks/${taskId}`, payload);
  return response.data;
}

export async function deleteTask(taskId: string) {
  await apiClient.delete(`/tasks/${taskId}`);
}

export async function listTaskComments(taskId: string) {
  const response = await apiClient.get<TaskComment[]>(`/tasks/${taskId}/comments`);
  return response.data;
}

export async function createTaskComment(taskId: string, message: string) {
  const response = await apiClient.post<TaskComment>(`/tasks/${taskId}/comments`, { message });
  return response.data;
}

export async function listTaskHistory(taskId: string) {
  const response = await apiClient.get<TaskHistoryEntry[]>(`/tasks/${taskId}/history`);
  return response.data;
}

export async function listTaskAttachments(taskId: string) {
  const response = await apiClient.get<DocumentRecord[]>(`/tasks/${taskId}/attachments`);
  return response.data;
}

export async function listTaskTemplates() {
  const response = await apiClient.get<TaskTemplate[]>("/tasks/templates");
  return response.data;
}

export async function createTaskTemplate(payload: TaskTemplatePayload) {
  const response = await apiClient.post<TaskTemplate>("/tasks/templates", payload);
  return response.data;
}

export async function generateDueTasks() {
  const response = await apiClient.post<{ generated_count: number; tasks: TaskItem[] }>(
    "/tasks/templates/generate-due",
  );
  return response.data;
}
