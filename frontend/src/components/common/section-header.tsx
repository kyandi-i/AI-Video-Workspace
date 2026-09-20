import type { ReactNode } from "react";

export function SectionHeader({
  title,
  description,
  metadata,
  actions,
  id,
}: {
  title: string;
  description?: string;
  metadata?: ReactNode;
  actions?: ReactNode;
  id?: string;
}) {
  return (
    <header className="section-header">
      <div>
        <div className="section-title-row">
          <h2 id={id}>{title}</h2>
          {metadata && <span className="section-metadata">{metadata}</span>}
        </div>
        {description && <p>{description}</p>}
      </div>
      {actions && <div className="header-actions">{actions}</div>}
    </header>
  );
}
