import type { BadgeTone } from "@/components/ui/badge";

export type EnumDisplay = { label: string; tone: BadgeTone };

// Keep machine values intact. Every enum domain supplies an exhaustive display map;
// components never derive user-facing text by splitting or title-casing values.
export function enumOptions<Value extends string>(
  values: readonly Value[],
  display: Record<Value, EnumDisplay>,
) {
  return values.map((value) => ({ value, label: display[value].label }));
}
