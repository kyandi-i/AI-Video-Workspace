import { requestJson } from "@/api/client";
import type { Character, CharacterState, ShotState, OwnerKind } from "./types";
export const characterApi = {
  list: (project: string, search = "", deleted = false) =>
    requestJson<Character[]>(
      `/projects/${project}/characters?${new URLSearchParams({ search, include_deleted: String(deleted) })}`,
    ),
  detail: (id: string) => requestJson<Character>(`/characters/${id}`),
  states: (id: string, deleted = false) =>
    requestJson<CharacterState[]>(
      `/characters/${id}/states?include_deleted=${deleted}`,
    ),
  create: (project: string, data: Record<string, string>) =>
    requestJson<Character>(`/projects/${project}/characters`, "POST", data),
  createState: (id: string, data: Record<string, string>) =>
    requestJson<CharacterState>(`/characters/${id}/states`, "POST", data),
  update: (kind: OwnerKind, id: string, data: Record<string, string>) =>
    requestJson(`/${kind}/${id}`, "PATCH", data),
  remove: (kind: OwnerKind, id: string) =>
    requestJson(`/${kind}/${id}`, "DELETE"),
  restore: (kind: OwnerKind, id: string) =>
    requestJson(`/${kind}/${id}/restore`, "POST"),
  move: (id: string, direction: "up" | "down") =>
    requestJson<CharacterState[]>(`/character-states/${id}/move`, "POST", {
      direction,
    }),
  asset: (kind: OwnerKind, id: string, asset: string, remove = false) =>
    requestJson(
      `/${kind}/${id}/assets${remove ? `/${asset}` : ""}`,
      remove ? "DELETE" : "POST",
      remove ? undefined : { asset_id: asset },
    ),
  shotStates: (id: string) =>
    requestJson<ShotState[]>(`/shots/${id}/character-states`),
  shot: (shot: string, state: string, remove = false) =>
    requestJson<ShotState[]>(
      `/shots/${shot}/character-states${remove ? `/${state}` : ""}`,
      remove ? "DELETE" : "POST",
      remove ? undefined : { character_state_id: state },
    ),
};
