import type { Entity } from "@/features/projects/types";
export interface Scene extends Entity {
  project_id: string;
  script_id: string;
  script_node_id: string;
  name: string;
  description: string;
  fixed_constraints: string;
  negative_constraints: string;
  order_index: number;
  shot_count: number;
}
export type SceneInput = Pick<
  Scene,
  "name" | "description" | "fixed_constraints" | "negative_constraints"
>;
