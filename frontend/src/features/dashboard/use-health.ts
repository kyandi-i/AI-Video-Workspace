import { useQuery } from "@tanstack/react-query";
import { z } from "zod";
import { getJson } from "@/api/client";

const healthSchema = z.object({
  status: z.literal("ok"),
  app: z.literal("ai-video-workspace"),
  version: z.string(),
  phase: z.number(),
  storage_initialized: z.boolean(),
});

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => healthSchema.parse(await getJson("/health")),
    retry: 1,
    refetchInterval: 15_000,
  });
}
