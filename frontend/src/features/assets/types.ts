import type { Entity, Project } from "@/features/projects/types";
import type { Shot } from "@/features/shots/types";
export const assetTypes = [
  "IMAGE",
  "VIDEO",
  "STORYBOARD_6GRID",
  "OTHER",
] as const;
export type AssetType = (typeof assetTypes)[number];
export interface Tag extends Entity {
  name: string;
}
export interface Asset extends Entity {
  name: string;
  description: string;
  asset_type: AssetType;
  original_filename: string;
  storage_path: string;
  thumbnail_path: string;
  mime_type: string;
  file_size: number;
  width: number | null;
  height: number | null;
  duration_seconds: number | null;
  tags: Tag[];
}
export interface AssetDetail extends Asset {
  video_results: (Entity & { shot_id: string; version: number; is_selected: boolean })[];
  storyboards: (Entity & {
    shot_id: string;
    version: number;
    is_selected: boolean;
  })[];
  projects: Project[];
  shots: Shot[];
  characters: (Entity & { project_id: string; name: string })[];
  character_states: (Entity & { character_id: string; name: string })[];
}
export type AssetInput = Pick<Asset, "name" | "description" | "asset_type">;
export type AssetFilters = {
  search?: string;
  asset_type?: string;
  tag_id?: string;
  project_id?: string;
  shot_id?: string;
};
