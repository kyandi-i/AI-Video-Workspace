import { requestJson } from "@/api/client";
import type { Scene, SceneInput } from "./types";
export const sceneApi = {
  list: (projectId: string) =>
    requestJson<Scene[]>(`${"/projects/" + projectId}/scenes`),
  detail: (id: string) => requestJson<Scene>(`/scenes/${id}`),
  create: (projectId: string, data: SceneInput & { script_id: string }) =>
    requestJson<Scene>(`/projects/${projectId}/scenes`, "POST", data),
  update: (id: string, data: SceneInput) =>
    requestJson<Scene>(`/scenes/${id}`, "PATCH", data),
  remove: (id: string) => requestJson<void>(`/scenes/${id}`, "DELETE"),
};
