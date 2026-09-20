import type { ReactNode } from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function EntityCard({
  name,
  metadata,
  status,
  preview,
  selected = false,
  onSelect,
  className,
}: {
  name: string;
  metadata?: ReactNode;
  status?: ReactNode;
  preview?: ReactNode;
  selected?: boolean;
  onSelect?: () => void;
  className?: string;
}) {
  const content = (
    <>
      {preview}
      <div className="entity-info">
        <div className="entity-title">
          <span>{name}</span>
          {status}
        </div>
        {metadata && <div className="entity-metadata">{metadata}</div>}
      </div>
    </>
  );
  return (
    <Card className={cn("entity-card", selected && "is-selected", className)}>
      {onSelect ? (
        <button
          className="entity-hit-area"
          aria-pressed={selected}
          onClick={onSelect}
        >
          {content}
        </button>
      ) : (
        content
      )}
    </Card>
  );
}
