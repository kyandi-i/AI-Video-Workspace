import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { QueryState, QueryErrors } from "@/components/common/query-state";
import { initialFilters, useTemplates, type Template } from "./api";
import { SamplePreview, TemplateFilters, TemplateSummary } from "./components";
import "./templates.css";

export function PromptTemplatePicker({
  projectId,
  onSelect,
  disabled = false,
}: {
  projectId: string;
  onSelect?: (template: Template) => void;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [filters, setFilters] = useState(initialFilters);
  const [selectedId, setSelectedId] = useState("");
  const [previewId, setPreviewId] = useState("");
  const query = useTemplates({
    ...filters,
    project_id: projectId,
    include_global: "true",
  });
  const preview = query.data?.find((t) => t.id === previewId);
  // Selection is local to this mounted Shot Workspace, never written to Shot.
  return (
    <section className="template-shot-entry" aria-label="Prompt Template">
      <div className="row-actions">
        <h3>Prompt Template</h3>
        <Button
          variant="secondary"
          disabled={disabled}
          onClick={() => setOpen(true)}
        >
          Browse Templates
        </Button>
        {selectedId && (
          <span className="muted-copy">已选择模板 · 仅本次浏览</span>
        )}
      </div>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="template-picker">
          <DialogHeader>
            <DialogTitle>Prompt Template Picker</DialogTitle>
            <DialogDescription>
              Global + 当前项目 · 选择仅用于当前浏览
            </DialogDescription>
          </DialogHeader>
          <TemplateFilters value={filters} onChange={setFilters} />
          <div className="template-picker-body">
            <div className="template-list">
              {!query.data ? (
                <QueryState queries={[query]} />
              ) : (
                <>
                  <QueryErrors queries={[query]} />
                  {!query.data.length && <p>没有匹配的模板。</p>}
                  {query.data.map((t) => (
                    <article className="template-row" key={t.id}>
                      <TemplateSummary template={t} />
                      <div className="row-actions">
                        <Button
                          variant="secondary"
                          onClick={() => setPreviewId(t.id)}
                        >
                          Preview Template
                        </Button>
                        <Button
                          onClick={() => {
                            setSelectedId(t.id);
                            setPreviewId(t.id);
                            onSelect?.(t);
                          }}
                        >
                          {selectedId === t.id ? "Selected" : "Select Template"}
                        </Button>
                      </div>
                    </article>
                  ))}
                </>
              )}
            </div>
            {preview && (
              <div className="template-picker-preview">
                <h3>{preview.name}</h3>
                <pre>{preview.template_content}</pre>
                <SamplePreview
                  key={preview.id}
                  content={preview.template_content}
                />
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </section>
  );
}
