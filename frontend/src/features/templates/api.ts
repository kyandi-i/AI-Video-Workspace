import { useQuery } from "@tanstack/react-query";
import { requestJson } from "@/api/client";

export const categories = [
  { value: "STORYBOARD_6GRID", label: "Storyboard 6-Grid" },
  { value: "VIDEO_GENERATION", label: "Video Generation" },
  { value: "CHARACTER_IMAGE", label: "Character Image" },
  { value: "SCENE_IMAGE", label: "Scene Image" },
  { value: "IMAGE_REFERENCE", label: "Image Reference" },
  { value: "START_END_FRAME", label: "Start / End Frame" },
  { value: "OTHER", label: "Other" },
];
export const scopes = [
  { value: "GLOBAL", label: "Global" },
  { value: "PROJECT", label: "Project" },
];
export interface Template {
  id: string;
  scope: string;
  project_id: string | null;
  name: string;
  description: string | null;
  category: string;
  template_content: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}
export interface Placeholder {
  key: string;
  label: string;
  description: string;
  group: string;
  example: string;
}
export interface Filters {
  search: string;
  scope: string;
  category: string;
  include_deleted?: string;
  project_id?: string;
  include_global?: string;
}
export const initialFilters: Filters = {
  search: "",
  scope: "all",
  category: "all",
};
export function useTemplates(filters: Filters) {
  const params = new URLSearchParams(
    Object.entries(filters).filter(([, v]) => v && v !== "all"),
  );
  return useQuery({
    queryKey: ["templates", filters],
    queryFn: () => requestJson<Template[]>(`/prompt-templates?${params}`),
  });
}
export function usePlaceholders() {
  return useQuery({
    queryKey: ["template-placeholders"],
    queryFn: () => requestJson<Placeholder[]>("/prompt-templates/placeholders"),
    staleTime: Infinity,
  });
}
export const samplePreview = (template_content: string) =>
  requestJson<{ rendered_content: string }>(
    "/prompt-templates/preview",
    "POST",
    { template_content },
  );
export const categoryLabel = (value: string) =>
  categories.find((c) => c.value === value)?.label ?? "Other";
