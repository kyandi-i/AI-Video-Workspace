import { useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { characterApi } from "./api";
export const characterKeys = {
  project: (id: string) => ["characters", id] as const,
  detail: (project: string, id: string) =>
    ["characters", project, "detail", id] as const,
  states: (project: string, id: string, deleted = false) =>
    ["characters", project, "states", id, deleted] as const,
  shot: (id: string) => ["shot-characters", id] as const,
};
export const useCharacters = (project: string, search = "", deleted = false) =>
  useQuery({
    queryKey: [...characterKeys.project(project), "list", search, deleted],
    queryFn: () => characterApi.list(project, search, deleted),
  });
export const useCharacter = (project: string, id: string) =>
  useQuery({
    queryKey: characterKeys.detail(project, id),
    queryFn: () => characterApi.detail(id),
  });
export const useStates = (project: string, id: string, deleted = false) =>
  useQuery({
    queryKey: characterKeys.states(project, id, deleted),
    queryFn: () => characterApi.states(id, deleted),
    enabled: Boolean(id),
  });
export const useShotStates = (id: string) =>
  useQuery({
    queryKey: characterKeys.shot(id),
    queryFn: () => characterApi.shotStates(id),
  });
export function useCharacterActions(project: string) {
  const client = useQueryClient();
  const busy = useRef(false);
  const mutation = useMutation({
    mutationFn: (action: () => Promise<unknown>) => action(),
    onSuccess: async () => {
      await Promise.all([
        client.invalidateQueries({ queryKey: ["shot-workspace"] }),
        client.invalidateQueries({ queryKey: characterKeys.project(project) }),
        client.invalidateQueries({ queryKey: ["shot-characters"] }),
        client.invalidateQueries({ queryKey: ["assets", "detail"] }),
      ]);
    },
  });
  return {
    ...mutation,
    run: async (action: () => Promise<unknown>) => {
      if (busy.current) return;
      busy.current = true;
      try {
        return await mutation.mutateAsync(action);
      } finally {
        busy.current = false;
      }
    },
  };
}
