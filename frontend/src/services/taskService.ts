import { apiClient } from "./apiClient";

export type TaskItem = {
  id: string;
  organization_id: string;
  property_id?: string | null;
  unit_id?: string | null;
  title: string;
  description?: string | null;
  category: string;
  priority: string;
  status: string;
  due_date?: string | null;
  assignee_name?: string | null;
  source: string;
};

export type TaskPayload = {
  property_id?: string | null;
  unit_id?: string | null;
  title: string;
  description?: string | null;
  category: string;
  priority: string;
  status: string;
  due_date?: string | null;
  assignee_name?: string | null;
  source: string;
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
