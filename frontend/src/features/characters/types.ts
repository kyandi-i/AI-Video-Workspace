import type { Entity } from "@/features/projects/types";
import type { Asset } from "@/features/assets/types";
export interface Character extends Entity {
  project_id: string;
  name: string;
  description: string;
  notes: string | null;
  state_count: number;
  asset_count: number;
  assets: Asset[];
}
export interface CharacterState extends Entity {
  character_id: string;
  name: string;
  description: string;
  order_index: number;
  shot_usage_count: number;
  assets: Asset[];
}
export interface ShotState extends CharacterState {
  character_name: string;
}
export type OwnerKind = "characters" | "character-states";
