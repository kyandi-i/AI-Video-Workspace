import { requestJson } from "@/api/client";

export interface ProviderSettings {
  provider: string;
  api_base_url: string;
  model: string;
  api_key_configured: boolean;
}
export interface PromptPreview {
  template_id: string;
  template_name: string;
  rendered_input: string;
  context: Record<string, string>;
  input_hash: string;
}
export interface PromptRecord {
  id: string;
  shot_id: string;
  template_id: string;
  template_name: string;
  rendered_input: string;
  generated_content: string;
  edited_content: string | null;
  effective_content: string;
  version: number;
  is_selected: boolean;
  prompt_type: string;
  template_content: string;
  context_json: Record<string, string>;
  input_hash: string;
  provider: string;
  model_name: string;
  created_at: string;
}
export const promptApi = {
  history: (shotId: string) =>
    requestJson<PromptRecord[]>(`/shots/${shotId}/prompts`),
  edit: (id: string, content: string) =>
    requestJson<PromptRecord>(`/prompts/${id}`, "PATCH", {
      edited_content: content,
    }),
  select: (id: string) =>
    requestJson<PromptRecord>(`/prompts/${id}/select`, "POST"),
  regenerate: (id: string, inputHash: string, operationId: string) =>
    requestJson<PromptRecord>(
      `/prompts/${id}/regenerate`,
      "POST",
      { input_hash: inputHash, operation_id: operationId },
      undefined,
      65_000,
    ),
  settings: () => requestJson<ProviderSettings>("/settings/ai"),
  preview: (shotId: string, templateId: string) =>
    requestJson<PromptPreview>(`/shots/${shotId}/prompts/preview`, "POST", {
      template_id: templateId,
    }),
  latest: (shotId: string) =>
    requestJson<PromptRecord | null>(`/shots/${shotId}/prompts/latest`),
  generate: (shotId: string, preview: PromptPreview, operationId: string) =>
    requestJson<PromptRecord>(
      `/shots/${shotId}/prompts/generate`,
      "POST",
      {
        template_id: preview.template_id,
        input_hash: preview.input_hash,
        operation_id: operationId,
      },
      undefined,
      65_000,
    ),
};
