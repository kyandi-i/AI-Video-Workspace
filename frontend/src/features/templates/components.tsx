import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Choice } from "@/components/common/entity-form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  categories,
  scopes,
  categoryLabel,
  samplePreview,
  type Filters,
  type Template,
} from "./api";

export function TemplateFilters({
  value,
  onChange,
}: {
  value: Filters;
  onChange: (value: Filters) => void;
}) {
  return (
    <div className="template-filters">
      <Input
        aria-label="Search templates"
        placeholder="Search name or description…"
        maxLength={255}
        value={value.search}
        onChange={(e) => onChange({ ...value, search: e.target.value })}
      />
      <Choice
        label="Scope filter"
        value={value.scope}
        onChange={(scope) => onChange({ ...value, scope })}
        options={[{ value: "all", label: "All scopes" }, ...scopes]}
      />
      <Choice
        label="Category filter"
        value={value.category}
        onChange={(category) => onChange({ ...value, category })}
        options={[{ value: "all", label: "All categories" }, ...categories]}
      />
    </div>
  );
}
export function TemplateSummary({ template }: { template: Template }) {
  return (
    <div className="template-summary">
      <h3>{template.name}</h3>
      <div className="row-actions">
        <Badge>{categoryLabel(template.category)}</Badge>
        <Badge>{template.scope === "GLOBAL" ? "Global" : "Project"}</Badge>
        {template.deleted_at && <Badge>Deleted</Badge>}
      </div>
      <p>{template.description || "暂无描述"}</p>
      <small>Updated {new Date(template.updated_at).toLocaleString()}</small>
    </div>
  );
}
export function SamplePreview({ content }: { content: string }) {
  const [requested, setRequested] = useState("");
  const preview = useMutation({ mutationFn: samplePreview });
  return (
    <section className="template-preview" aria-label="Sample Preview">
      <div className="row-actions">
        <h3>Sample Preview</h3>
        <Button
          type="button"
          variant="secondary"
          disabled={!content.trim() || preview.isPending}
          onClick={() => {
            setRequested(content);
            preview.mutate(content);
          }}
        >
          Preview
        </Button>
      </div>
      <p className="muted-copy">Preview uses sample data · 固定示例文本替换</p>
      {preview.error && (
        <p role="alert" className="error-banner">
          {preview.error.message}
        </p>
      )}
      {preview.data && requested === content && (
        <pre>{preview.data.rendered_content}</pre>
      )}
      {preview.data && requested !== content && (
        <p className="muted-copy">正文已修改，请重新预览。</p>
      )}
    </section>
  );
}
