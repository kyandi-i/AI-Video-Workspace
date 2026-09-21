import { requestJson } from "@/api/client";
import type { Shot, ShotInput } from "./types";
export const shotApi = {
  list: (projectId: string) =>
    requestJson<Shot[]>(`${"/projects/" + projectId}/shots`),
  detail: (id: string) => requestJson<Shot>(`/shots/${id}`),
  create: (sceneId: string, data: ShotInput & { project_id: string }) =>
    requestJson<Shot>(`/scenes/${sceneId}/shots`, "POST", data),
  update: (id: string, data: ShotInput) =>
    requestJson<Shot>(`/shots/${id}`, "PATCH", data),
  remove: (id: string) => requestJson<void>(`/shots/${id}`, "DELETE"),
  move: (id: string, direction: "up" | "down") =>
    requestJson<Shot[]>(`/shots/${id}/move`, "POST", { direction }),
  byScene: (id: string) => requestJson<Shot[]>(`/scenes/${id}/shots`),
};
