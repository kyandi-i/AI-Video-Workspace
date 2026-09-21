import type { QueryClient } from "@tanstack/react-query";
import { shotsKeys } from "@/api/query-keys";
import type { Shot } from "./types";

// Cascade deletion must also evict previously opened details before Back navigation.
export function removeShotDetails(
  client: QueryClient,
  projectId: string,
  sceneIds?: string[],
) {
  for (const [queryKey, shot] of client.getQueriesData<Shot>({
    queryKey: shotsKeys.details,
  })) {
    if (
      shot?.project_id === projectId &&
      (!sceneIds || sceneIds.includes(shot.scene_id))
    ) {
      client.removeQueries({ queryKey, exact: true });
    }
  }
  for (const sceneId of sceneIds ?? [])
    client.removeQueries({ queryKey: shotsKeys.byScene(sceneId) });
}
