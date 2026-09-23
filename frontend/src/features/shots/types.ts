import type { Entity } from "@/features/projects/types";
export const shotStatuses = [
  "DRAFT",
  "ASSET_PREPARING",
  "STORYBOARD_PROMPT_READY",
  "STORYBOARD_READY",
  "VIDEO_PROMPT_READY",
  "VIDEO_GENERATING",
  "REVIEW",
  "DONE",
] as const;
export type ShotStatus = (typeof shotStatuses)[number];
export interface Shot extends Entity {
  project_id: string;
  scene_id: string;
  shot_code: string;
  title: string;
  description: string;
  duration_seconds: number;
  order_index: number;
  status: ShotStatus;
  creative_requirement: string;
  main_action: string | null;
  key_constraints: string | null;
  negative_constraints: string | null;
  free_notes: string | null;
}
export type ShotInput = Pick<
  Shot,
  | "shot_code"
  | "title"
  | "description"
  | "duration_seconds"
  | "status"
  | "creative_requirement"
>;
