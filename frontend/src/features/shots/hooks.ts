import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { projectsKeys, scenesKeys, shotsKeys } from "@/api/query-keys";
import { shotApi } from "./api";
import type { ShotInput } from "./types";

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
    onSuccess: (shots) =>
      Promise.all([
        client.invalidateQueries({ queryKey: shotsKeys.byProject(projectId) }),
        ...(shots[0]
          ? [
              client.invalidateQueries({
                queryKey: shotsKeys.byScene(shots[0].scene_id),
              }),
            ]
          : []),
        ...shots.map((shot) =>
          client.invalidateQueries({ queryKey: shotsKeys.detail(shot.id) }),
        ),
      ]),
  });
  return { save, remove, move };
}
