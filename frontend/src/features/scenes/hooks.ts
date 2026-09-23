import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { projectsKeys, scenesKeys, shotsKeys } from "@/api/query-keys";
import { sceneApi } from "./api";
import type { SceneInput } from "./types";
import { removeShotDetails } from "@/features/shots/cache";

export const useScenes = (id: string) =>
  useQuery({
    queryKey: scenesKeys.byProject(id),
    queryFn: () => sceneApi.list(id),
  });
export function useSceneMutations(projectId: string) {
  const client = useQueryClient();
  const refresh = () =>
    Promise.all(
      [
        ["shot-workspace"],
        scenesKeys.byProject(projectId),
        projectsKeys.stats(projectId),
      ].map((queryKey) => client.invalidateQueries({ queryKey })),
    );
  const save = useMutation({
    mutationFn: ({
      id,
      scriptId,
      data,
    }: {
      id?: string;
      scriptId: string;
      data: SceneInput;
    }) =>
      id
        ? sceneApi.update(id, data)
        : sceneApi.create(projectId, { ...data, script_id: scriptId }),
    onSuccess: refresh,
  });
  const remove = useMutation({
    mutationFn: sceneApi.remove,
    onSuccess: (_, id) => {
      removeShotDetails(client, projectId, [id]);
      return Promise.all([
        refresh(),
        ...[shotsKeys.byScene(id), shotsKeys.byProject(projectId)].map(
          (queryKey) => client.invalidateQueries({ queryKey }),
        ),
      ]);
    },
  });
  return { save, remove };
}
