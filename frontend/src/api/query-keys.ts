export const projectsKeys = {
  all: ["projects"] as const,
  detail: (id: string) => ["project", id] as const,
  stats: (id: string) => ["project", id, "stats"] as const,
};
export const scriptsKeys = {
  byProject: (id: string) => ["scripts", id] as const,
};
export const scenesKeys = {
  byProject: (id: string) => ["scenes", id] as const,
};
export const shotsKeys = {
  details: ["shot"] as const,
  byProject: (id: string) => ["shots", "project", id] as const,
  byScene: (id: string) => ["shots", "scene", id] as const,
  detail: (id: string) => ["shot", id] as const,
};
