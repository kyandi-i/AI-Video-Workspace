import { requestJson } from "@/api/client";
import type { Script, ScriptInput } from "./types";
export const scriptApi = {
  list: (projectId: string) =>
    requestJson<Script[]>(`${"/projects/" + projectId}/scripts`),
  detail: (id: string) => requestJson<Script>(`/scripts/${id}`),
  create: (projectId: string, data: ScriptInput) =>
    requestJson<Script>(`/projects/${projectId}/scripts`, "POST", data),
  update: (id: string, data: ScriptInput) =>
    requestJson<Script>(`/scripts/${id}`, "PATCH", data),
  remove: (id: string) => requestJson<void>(`/scripts/${id}`, "DELETE"),
};
