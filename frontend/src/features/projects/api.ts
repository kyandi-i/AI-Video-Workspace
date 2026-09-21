import { requestJson } from "@/api/client";
import type { Project, ProjectInput, ProjectStats } from "./types";
export const projectApi = {
  list: () => requestJson<Project[]>(`/projects`),
  detail: (id: string) => requestJson<Project>(`/projects/${id}`),
  create: (data: ProjectInput) =>
    requestJson<Project>(`/projects`, "POST", data),
  update: (id: string, data: ProjectInput) =>
    requestJson<Project>(`/projects/${id}`, "PATCH", data),
  remove: (id: string) => requestJson<void>(`/projects/${id}`, "DELETE"),
  stats: (id: string) => requestJson<ProjectStats>(`/projects/${id}/stats`),
};
