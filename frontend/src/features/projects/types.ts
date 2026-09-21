export interface Entity {
  id: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}
export const projectStatuses = [
  "DRAFT",
  "ACTIVE",
  "PAUSED",
  "COMPLETED",
  "ARCHIVED",
] as const;
export type ProjectStatus = (typeof projectStatuses)[number];
export interface Project extends Entity {
  name: string;
  description: string;
  status: ProjectStatus;
}
export type ProjectInput = Pick<Project, "name" | "description" | "status">;
export interface ProjectStats {
  scripts: number;
  scenes: number;
  shots: number;
}
