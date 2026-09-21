import { requestJson } from "@/api/client";
import type {
  Asset,
  AssetDetail,
  AssetFilters,
  AssetInput,
  AssetType,
  Tag,
} from "./types";
export const assetApi = {
  list: (filters: AssetFilters, offset: number) =>
    requestJson<Asset[]>(
      `/assets?${new URLSearchParams({ ...filters, offset: String(offset), limit: "60" })}`,
    ),
  detail: (id: string) => requestJson<AssetDetail>(`/assets/${id}`),
  update: (id: string, data: AssetInput) =>
    requestJson<AssetDetail>(`/assets/${id}`, "PATCH", data),
  remove: (id: string) => requestJson<void>(`/assets/${id}`, "DELETE"),
  upload: (file: File, type?: AssetType) =>
    requestJson<AssetDetail>(
      `/assets/upload?${new URLSearchParams({ filename: file.name, ...(type ? { asset_type: type } : {}) })}`,
      "POST",
      undefined,
      file,
    ),
  tags: () => requestJson<Tag[]>("/tags"),
  addTag: async (id: string, name: string) => {
    const tag = await requestJson<Tag>("/tags", "POST", { name });
    return requestJson<AssetDetail>(`/assets/${id}/tags/${tag.id}`, "POST");
  },
  removeTag: (id: string, tagId: string) =>
    requestJson<AssetDetail>(`/assets/${id}/tags/${tagId}`, "DELETE"),
  bind: (
    id: string,
    kind: "projects" | "shots",
    owner: string,
    remove = false,
  ) =>
    requestJson<AssetDetail>(
      `/${kind}/${owner}/assets${remove ? `/${id}` : ""}`,
      remove ? "DELETE" : "POST",
      remove ? undefined : { asset_id: id },
    ),
  thumbnail: (id: string) => `/api/assets/${id}/thumbnail`,
  file: (id: string) => `/api/assets/${id}/file`,
};
