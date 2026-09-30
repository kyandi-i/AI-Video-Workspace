import { requestJson } from "@/api/client";
import type { Asset } from "@/features/assets/types";

export interface Storyboard {
  id: string;
  shot_id: string;
  asset_id: string;
  source_prompt_record_id: string | null;
  storyboard_type: "GRID_6";
  version: number;
  is_selected: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  asset: Asset;
  source_prompt: {
    id: string;
    version: number;
    prompt_type: string;
    is_edited: boolean;
  } | null;
}

export const storyboardApi = {
  history: (shotId: string) =>
    requestJson<Storyboard[]>(`/shots/${shotId}/storyboards`),
  create: (
    shotId: string,
    assetId: string,
    sourceId: string | null,
    notes: string,
  ) =>
    requestJson<Storyboard>(`/shots/${shotId}/storyboards`, "POST", {
      asset_id: assetId,
      source_prompt_record_id: sourceId,
      notes: notes || null,
    }),
  upload: (
    shotId: string,
    file: File,
    sourceId: string | null,
    notes: string,
  ) =>
    requestJson<Storyboard>(
      `/shots/${shotId}/storyboards/import?${new URLSearchParams({
        filename: file.name,
        ...(sourceId ? { source_prompt_record_id: sourceId } : {}),
        ...(notes ? { notes } : {}),
      })}`,
      "POST",
      undefined,
      file,
    ),
  select: (id: string) =>
    requestJson<Storyboard>(`/storyboards/${id}/select`, "POST"),
  remove: (id: string) => requestJson<void>(`/storyboards/${id}`, "DELETE"),
};
