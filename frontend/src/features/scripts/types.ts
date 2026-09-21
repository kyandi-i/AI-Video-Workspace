import type { Entity } from "@/features/projects/types";
export interface Script extends Entity {
  project_id: string;
  name: string;
  description: string;
}
export type ScriptInput = Pick<Script, "name" | "description">;
