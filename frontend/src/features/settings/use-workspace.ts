import { useQuery } from "@tanstack/react-query";
import { z } from "zod";
import { getJson } from "@/api/client";

const schema = z.object({
  workspace_root: z.string(),
  database_path: z.string(),
  initialized: z.boolean(),
});
export function useWorkspace() {
  return useQuery({
    queryKey: ["workspace"],
    queryFn: async () => schema.parse(await getJson("/settings/workspace")),
    retry: 1,
  });
}
