import { Badge } from "@/components/ui/badge";
import { statusDisplay, type WorkflowStatus } from "@/lib/status-display";

export function StatusBadge({ status }: { status: WorkflowStatus }) {
  const display = statusDisplay[status];
  return <Badge tone={display.tone}>{display.label}</Badge>;
}
