import { requestJson } from "@/api/client";
import type { Asset } from "@/features/assets/types";
import type { Entity } from "@/features/projects/types";

export interface VideoResult extends Entity {
  shot_id: string;
  asset_id: string;
  source_storyboard_id: string | null;
  source_prompt_record_id: string | null;
  version: number;
  is_selected: boolean;
  notes: string | null;
  asset: Asset;
  source_storyboard: { id: string; version: number; is_deleted: boolean } | null;
  source_prompt: { id: string; version: number; prompt_type: string; is_edited: boolean } | null;
}
export interface VideoSources {
  source_storyboard_id: string | null;
  source_prompt_record_id: string | null;
  notes: string | null;
}
export const videoApi = {
  history: (shotId: string) => requestJson<VideoResult[]>(`/shots/${shotId}/video-results?include_deleted=true`),
  create: (shotId: string, assetId: string, sources: VideoSources) => requestJson<VideoResult>(`/shots/${shotId}/video-results`, "POST", { asset_id: assetId, ...sources }),
  upload: (shotId: string, file: File, sources: VideoSources) => requestJson<VideoResult>(`/shots/${shotId}/video-results/import?${new URLSearchParams({ filename: file.name, ...Object.fromEntries(Object.entries(sources).filter(([,v]) => v !== null)) })}`, "POST", undefined, file),
  select: (id: string) => requestJson<VideoResult>(`/video-results/${id}/select`, "POST"),
  remove: (id: string) => requestJson<void>(`/video-results/${id}`, "DELETE"),
  restore: (id: string) => requestJson<VideoResult>(`/video-results/${id}/restore`, "POST"),
};
