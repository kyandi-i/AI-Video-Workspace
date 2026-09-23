import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { assetApi } from "./api";
import { shotsKeys } from "@/api/query-keys";
import { shotApi } from "@/features/shots/api";
import type { AssetFilters, AssetInput, AssetType } from "./types";
export const assetsKeys = {
  lists: ["assets", "lists"] as const,
  list: (filters: AssetFilters) => ["assets", "lists", filters] as const,
  detail: (id: string) => ["assets", "detail", id] as const,
  tags: ["assets", "tags"] as const,
};
export const useAssets = (filters: AssetFilters) =>
  useInfiniteQuery({
    queryKey: assetsKeys.list(filters),
    initialPageParam: 0,
    queryFn: ({ pageParam }) => assetApi.list(filters, pageParam),
    getNextPageParam: (last, pages) =>
      last.length === 60 ? pages.length * 60 : undefined,
  });
export const useAsset = (id: string) =>
  useQuery({
    queryKey: assetsKeys.detail(id),
    queryFn: () => assetApi.detail(id),
  });
export const useTags = () =>
  useQuery({ queryKey: assetsKeys.tags, queryFn: assetApi.tags });
export const useBindingShots = (id: string) =>
  useQuery({
    queryKey: shotsKeys.byProject(id),
    queryFn: () => shotApi.list(id),
    enabled: Boolean(id),
  });
export function useAssetActions(id = "") {
  const client = useQueryClient();
  const mutation = useMutation({
    mutationFn: (action: () => Promise<unknown>) => action(),
    onSuccess: async () => {
      await Promise.all([
        client.invalidateQueries({ queryKey: ["shot-workspace"] }),
        client.invalidateQueries({ queryKey: assetsKeys.lists }),
        client.invalidateQueries({ queryKey: assetsKeys.tags }),
        ...(id
          ? [client.invalidateQueries({ queryKey: assetsKeys.detail(id) })]
          : []),
      ]);
    },
  });
  return {
    ...mutation,
    save: (data: AssetInput) =>
      mutation.mutateAsync(() => assetApi.update(id, data)),
    remove: () => mutation.mutateAsync(() => assetApi.remove(id)),
    addTag: (name: string) =>
      mutation.mutateAsync(() => assetApi.addTag(id, name)),
    removeTag: (tagId: string) =>
      mutation.mutateAsync(() => assetApi.removeTag(id, tagId)),
    bind: (kind: "projects" | "shots", owner: string, remove = false) =>
      mutation.mutateAsync(() => assetApi.bind(id, kind, owner, remove)),
    upload: (file: File, type?: AssetType) =>
      mutation.mutateAsync(() => assetApi.upload(file, type)),
  };
}
