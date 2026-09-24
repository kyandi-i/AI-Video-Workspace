import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { requestJson } from "@/api/client";
import { useProjects } from "@/features/projects/hooks";
import { PageHeader } from "@/components/common/page-header";
import { QueryState, QueryErrors } from "@/components/common/query-state";
import { Choice } from "@/components/common/entity-form";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { initialFilters, useTemplates, type Template } from "./api";
import { TemplateFilters, TemplateSummary } from "./components";
import { TemplateEditor } from "./template-editor";
import "./templates.css";

export function Component() {
  const { projectId } = useParams();
  const [filters, setFilters] = useState(initialFilters);
  const [deleted, setDeleted] = useState(false);
  const [editor, setEditor] = useState<Template | "new" | null>(null);
  const [action, setAction] = useState<{
    template: Template;
    kind: "delete" | "copy";
  } | null>(null);
  const [target, setTarget] = useState(projectId ?? "");
  const projects = useProjects();
  const query = useTemplates({
    ...filters,
    project_id: projectId,
    include_global: projectId ? "true" : undefined,
    include_deleted: String(deleted),
  });
  const client = useQueryClient();
  const mutation = useMutation({
    mutationFn: ({
      id,
      operation,
      project,
    }: {
      id: string;
      operation: string;
      project?: string;
    }) =>
      requestJson(
        `/prompt-templates/${id}${operation === "delete" ? "" : `/${operation}`}`,
        operation === "delete" ? "DELETE" : "POST",
        project ? { project_id: project } : undefined,
      ),
    onSuccess: async () => {
      setAction(null);
      await client.invalidateQueries({ queryKey: ["templates"] });
    },
  });
  return (
    <div className="workspace-page template-library">
      <PageHeader
        title="Prompt Templates"
        description={
          projectId ? "当前项目模板与可用 Global 模板" : "模板结构、格式与规则"
        }
        actions={
          <Button onClick={() => setEditor("new")}>Create Template</Button>
        }
      />
      <TemplateFilters value={filters} onChange={setFilters} />
      <label className="template-deleted-toggle">
        <input
          type="checkbox"
          checked={deleted}
          onChange={(e) => setDeleted(e.target.checked)}
        />{" "}
        Show deleted templates
      </label>
      {mutation.error && (
        <p role="alert" className="error-banner">
          {mutation.error.message}
        </p>
      )}
      {!query.data ? (
        <QueryState queries={[query]} />
      ) : (
        <>
          <QueryErrors queries={[query]} />
          {query.data.length === 0 && (
            <p className="template-empty">
              没有匹配的模板。调整筛选或创建第一个模板。
            </p>
          )}
          <div className="template-list">
            {query.data.map((t) => (
              <article key={t.id} className="template-row">
                <TemplateSummary template={t} />
                <div className="row-actions">
                  {t.deleted_at ? (
                    <Button
                      disabled={mutation.isPending}
                      onClick={() =>
                        mutation.mutate({ id: t.id, operation: "restore" })
                      }
                    >
                      Restore
                    </Button>
                  ) : (
                    <>
                      <Button variant="secondary" onClick={() => setEditor(t)}>
                        Edit
                      </Button>
                      <Button
                        variant="ghost"
                        disabled={mutation.isPending}
                        onClick={() =>
                          mutation.mutate({ id: t.id, operation: "duplicate" })
                        }
                      >
                        Duplicate
                      </Button>
                      {t.scope === "GLOBAL" && (
                        <Button
                          variant="ghost"
                          onClick={() => {
                            mutation.reset();
                            setAction({ template: t, kind: "copy" });
                          }}
                        >
                          Copy to Project
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        onClick={() => {
                          mutation.reset();
                          setAction({ template: t, kind: "delete" });
                        }}
                      >
                        Delete
                      </Button>
                    </>
                  )}
                </div>
              </article>
            ))}
          </div>
        </>
      )}
      {editor && (
        <TemplateEditor
          template={editor === "new" ? undefined : editor}
          projectId={projectId}
          onClose={() => setEditor(null)}
        />
      )}
      <Dialog
        open={!!action}
        onOpenChange={(open) => {
          if (!open && !mutation.isPending) setAction(null);
        }}
      >
        <DialogContent closeDisabled={mutation.isPending}>
          <DialogHeader>
            <DialogTitle>
              {action?.kind === "copy"
                ? "Copy Global → Project"
                : "Delete Template"}
            </DialogTitle>
            <DialogDescription>
              {action?.template.name} ·{" "}
              {action?.kind === "copy"
                ? "复制后独立维护，原模板不变。"
                : "软删除后可以恢复，名称仍保留。"}
            </DialogDescription>
          </DialogHeader>
          {action?.kind === "copy" &&
            (!projects.data ? (
              <QueryState queries={[projects]} />
            ) : (
              <Choice
                label="Target project"
                value={target}
                options={projects.data.map((p) => ({
                  value: p.id,
                  label: p.name,
                }))}
                onChange={setTarget}
                disabled={mutation.isPending}
              />
            ))}
          {mutation.error && (
            <p role="alert" className="error-banner">
              {mutation.error.message}
            </p>
          )}
          <DialogFooter>
            <Button
              variant="secondary"
              disabled={mutation.isPending}
              onClick={() => setAction(null)}
            >
              Cancel
            </Button>
            <Button
              disabled={
                mutation.isPending || (action?.kind === "copy" && !target)
              }
              onClick={() =>
                action &&
                mutation.mutate({
                  id: action.template.id,
                  operation:
                    action.kind === "copy" ? "copy-to-project" : "delete",
                  project: action.kind === "copy" ? target : undefined,
                })
              }
            >
              {action?.kind === "copy" ? "Confirm Copy" : "Confirm Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
