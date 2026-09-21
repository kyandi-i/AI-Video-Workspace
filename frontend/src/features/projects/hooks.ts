import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  projectsKeys,
  scenesKeys,
  scriptsKeys,
  shotsKeys,
} from "@/api/query-keys";
import { projectApi } from "./api";
import type { ProjectInput } from "./types";
import { removeShotDetails } from "@/features/shots/cache";
import type { Scene } from "@/features/scenes/types";

export const useProjects = () =>
  useQuery({ queryKey: projectsKeys.all, queryFn: projectApi.list });
export const useProject = (id: string) =>
  useQuery({
    queryKey: projectsKeys.detail(id),
    queryFn: () => projectApi.detail(id),
  });
export const useProjectStats = (id: string) =>
  useQuery({
    queryKey: projectsKeys.stats(id),
    queryFn: () => projectApi.stats(id),
  });
export function useProjectMutations() {
  const client = useQueryClient();
  const refresh = async (id?: string) => {
    await client.invalidateQueries({ queryKey: projectsKeys.all });
    if (id)
      await client.invalidateQueries({ queryKey: projectsKeys.detail(id) });
  };
  const save = useMutation({
    mutationFn: ({ id, data }: { id?: string; data: ProjectInput }) =>
      id ? projectApi.update(id, data) : projectApi.create(data),
    onSuccess: (project) => refresh(project.id),
  });
  const remove = useMutation({
    mutationFn: projectApi.remove,
    onSuccess: async (_, id) => {
      const scenes = client.getQueryData<Scene[]>(scenesKeys.byProject(id));
      removeShotDetails(
        client,
        id,
        scenes?.map((scene) => scene.id),
      );
      client.removeQueries({ queryKey: projectsKeys.detail(id) });
      client.removeQueries({ queryKey: scriptsKeys.byProject(id) });
      client.removeQueries({ queryKey: scenesKeys.byProject(id) });
      client.removeQueries({ queryKey: shotsKeys.byProject(id) });
      await refresh();
    },
  });
  return { save, remove };
}
