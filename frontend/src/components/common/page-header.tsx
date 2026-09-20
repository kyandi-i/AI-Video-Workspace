import type { ReactNode } from "react";

export function PageHeader({
  title,
  description,
  metadata,
  actions,
}: {
  title: string;
  description?: string;
  metadata?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="page-header">
      <div>
        <div className="page-title-row">
          <h1>{title}</h1>
          {metadata}
        </div>
        {description && <p>{description}</p>}
      </div>
      {actions && <div className="header-actions">{actions}</div>}
    </div>
  );
}
