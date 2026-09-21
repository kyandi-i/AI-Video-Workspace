import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { projectsKeys, scenesKeys, shotsKeys } from "@/api/query-keys";
import { shotApi } from "./api";
import type { Shot, ShotInput } from "./types";

export const useShots = (id: string) =>
  useQuery({
    queryKey: shotsKeys.byProject(id),
    queryFn: () => shotApi.list(id),
  });
export const useShot = (id: string) =>
  useQuery({
    queryKey: shotsKeys.detail(id),
    queryFn: () => shotApi.detail(id),
  });
export function useShotMutations(projectId: string) {
  const client = useQueryClient();
  const refresh = (sceneId: string, id?: string) =>
    Promise.all(
      [
        shotsKeys.byScene(sceneId),
        shotsKeys.byProject(projectId),
        scenesKeys.byProject(projectId),
        projectsKeys.stats(projectId),
        ...(id ? [shotsKeys.detail(id)] : []),
      ].map((queryKey) => client.invalidateQueries({ queryKey })),
    );
  const save = useMutation({
    mutationFn: ({
      id,
      sceneId,
      data,
    }: {
      id?: string;
      sceneId: string;
      data: ShotInput;
    }) =>
      id
        ? shotApi.update(id, data)
        : shotApi.create(sceneId, { ...data, project_id: projectId }),
    onSuccess: (shot) => refresh(shot.scene_id, shot.id),
  });
  const remove = useMutation({
    mutationFn: ({ id }: { id: string; sceneId: string }) => shotApi.remove(id),
    onSuccess: (_, shot) => refresh(shot.sceneId, shot.id),
  });
  const move = useMutation({
    mutationFn: ({ id, direction }: { id: string; direction: "up" | "down" }) =>
      shotApi.move(id, direction),
    onSuccess: async (shots) => {
      const sceneId = shots[0]?.scene_id;
      if (!sceneId) return;
      // Apply the server's canonical order in one cache update. Cancel older reads
      // first so a response from before the move cannot flash the previous order.
      await Promise.all(
        [
          shotsKeys.byProject(projectId),
          shotsKeys.byScene(sceneId),
          ...shots.map((shot) => shotsKeys.detail(shot.id)),
        ].map((queryKey) => client.cancelQueries({ queryKey })),
      );
      client.setQueryData<Shot[]>(shotsKeys.byProject(projectId), (current) => {
        if (!current) return current;
        const first = current.findIndex((shot) => shot.scene_id === sceneId);
        return current.flatMap((shot, index) =>
          index === first ? shots : shot.scene_id === sceneId ? [] : [shot],
        );
      });
      client.setQueryData(shotsKeys.byScene(sceneId), shots);
      for (const shot of shots)
        client.setQueryData(shotsKeys.detail(shot.id), shot);
    },
  });
  return { save, remove, move };
}
