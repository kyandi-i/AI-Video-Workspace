import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  projectsKeys,
  scenesKeys,
  scriptsKeys,
  shotsKeys,
} from "@/api/query-keys";
import { scriptApi } from "./api";
import type { ScriptInput } from "./types";
import type { Scene } from "@/features/scenes/types";
import { removeShotDetails } from "@/features/shots/cache";

export const useScripts = (id: string) =>
  useQuery({
    queryKey: scriptsKeys.byProject(id),
    queryFn: () => scriptApi.list(id),
  });
export function useScriptMutations(projectId: string) {
  const client = useQueryClient();
  const refresh = () =>
    Promise.all(
      [scriptsKeys.byProject(projectId), projectsKeys.stats(projectId)].map(
        (queryKey) => client.invalidateQueries({ queryKey }),
      ),
    );
  const save = useMutation({
    mutationFn: ({ id, data }: { id?: string; data: ScriptInput }) =>
      id ? scriptApi.update(id, data) : scriptApi.create(projectId, data),
    onSuccess: refresh,
  });
  const remove = useMutation({
    mutationFn: scriptApi.remove,
    onSuccess: (_, id) => {
      const scenes = client.getQueryData<Scene[]>(
        scenesKeys.byProject(projectId),
      );
      removeShotDetails(
        client,
        projectId,
        scenes
          ?.filter((scene) => scene.script_id === id)
          .map((scene) => scene.id),
      );
      return Promise.all([
        refresh(),
        ...[
          scenesKeys.byProject(projectId),
          shotsKeys.byProject(projectId),
        ].map((queryKey) => client.invalidateQueries({ queryKey })),
      ]);
    },
  });
  return { save, remove };
}
