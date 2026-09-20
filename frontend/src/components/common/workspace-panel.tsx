import { useId, type ReactNode } from "react";
import { SectionHeader } from "./section-header";
import { cn } from "@/lib/utils";

export function WorkspacePanel({
  title,
  description,
  metadata,
  actions,
  children,
  className,
}: {
  title: string;
  description?: string;
  metadata?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  const id = useId();
  return (
    <section className={cn("workspace-panel", className)} aria-labelledby={id}>
      <SectionHeader
        id={id}
        title={title}
        description={description}
        metadata={metadata}
        actions={actions}
      />
      <div className="panel-content">{children}</div>
    </section>
  );
}
