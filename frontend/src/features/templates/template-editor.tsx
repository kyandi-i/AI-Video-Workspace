import { useCallback, useRef, useState } from "react";
import { useBeforeUnload } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { requestJson } from "@/api/client";
import { useProjects } from "@/features/projects/hooks";
import { Choice } from "@/components/common/entity-form";
import { QueryState } from "@/components/common/query-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { categories, scopes, usePlaceholders, type Template } from "./api";
import { SamplePreview } from "./components";

export function TemplateEditor({
  template,
  projectId,
  onClose,
}: {
  template?: Template;
  projectId?: string;
  onClose: () => void;
}) {
  const initial = {
    name: template?.name ?? "",
    description: template?.description ?? "",
    scope: template?.scope ?? (projectId ? "PROJECT" : "GLOBAL"),
    project_id: template?.project_id ?? projectId ?? "",
    category: template?.category ?? "OTHER",
    template_content: template?.template_content ?? "",
  };
  const [values, setValues] = useState(initial);
  const [saved, setSaved] = useState(initial);
  const [id, setId] = useState(template?.id);
  const [discard, setDiscard] = useState(false);
  const area = useRef<HTMLTextAreaElement>(null);
  const busy = useRef(false);
  const registry = usePlaceholders();
  const projects = useProjects();
  const client = useQueryClient();
  const dirty = JSON.stringify(values) !== JSON.stringify(saved);
  const save = useMutation({
    mutationFn: () =>
      requestJson<Template>(
        id ? `/prompt-templates/${id}` : "/prompt-templates",
        id ? "PATCH" : "POST",
        {
          ...values,
          project_id: values.scope === "PROJECT" ? values.project_id : null,
        },
      ),
    onSuccess: async (result) => {
      setId(result.id);
      setSaved(values);
      await client.invalidateQueries({ queryKey: ["templates"] });
    },
  });
  useBeforeUnload(
    useCallback(
      (event) => {
        if (dirty || busy.current) {
          event.preventDefault();
          event.returnValue = "";
        }
      },
      [dirty],
    ),
  );
  const set = (key: keyof typeof values, value: string) =>
    setValues((v) => ({ ...v, [key]: value }));
  const close = () => {
    if (busy.current) return;
    if (dirty) setDiscard(true);
    else onClose();
  };
  const insert = (key: string) => {
    const input = area.current;
    if (!input) return;
    const start = input.selectionStart,
      end = input.selectionEnd,
      token = `{{${key}}}`;
    const next =
      values.template_content.slice(0, start) +
      token +
      values.template_content.slice(end);
    if (next.length > 100000) return;
    set("template_content", next);
    requestAnimationFrame(() => {
      input.focus();
      input.setSelectionRange(start + token.length, start + token.length);
    });
  };
  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) close();
      }}
    >
      <DialogContent
        className="template-editor"
        closeDisabled={save.isPending}
        onInteractOutside={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>Template Editor</DialogTitle>
          <DialogDescription>
            管理模板结构与规则 · 支持白名单变量和纯文本
          </DialogDescription>
        </DialogHeader>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            if (busy.current) return;
            busy.current = true;
            try {
              await save.mutateAsync();
            } catch {
              /* Retain draft. */
            } finally {
              busy.current = false;
            }
          }}
        >
          <div className="template-editor-body">
            <fieldset disabled={save.isPending} className="template-fields">
              <label htmlFor="template-name">Name</label>
              <Input
                id="template-name"
                required
                maxLength={255}
                value={values.name}
                onChange={(e) => set("name", e.target.value)}
              />
              <label htmlFor="template-description">Description</label>
              <Textarea
                id="template-description"
                maxLength={100000}
                rows={2}
                value={values.description}
                onChange={(e) => set("description", e.target.value)}
              />
              <div className="template-form-pair">
                <div>
                  <label>Scope</label>
                  <Choice
                    label="Template scope"
                    value={values.scope}
                    options={scopes}
                    onChange={(v) => set("scope", v)}
                    disabled={save.isPending}
                  />
                </div>
                <div>
                  <label>Category</label>
                  <Choice
                    label="Template category"
                    value={values.category}
                    options={categories}
                    onChange={(v) => set("category", v)}
                    disabled={save.isPending}
                  />
                </div>
              </div>
              {values.scope === "PROJECT" && (
                <div>
                  <label>Project</label>
                  {!projects.data ? (
                    <QueryState queries={[projects]} />
                  ) : (
                    <Choice
                      label="Template project"
                      value={values.project_id}
                      options={projects.data.map((p) => ({
                        value: p.id,
                        label: p.name,
                      }))}
                      onChange={(v) => set("project_id", v)}
                      disabled={save.isPending}
                    />
                  )}
                </div>
              )}
              <label htmlFor="template-content">Template Content</label>
              <Textarea
                ref={area}
                id="template-content"
                required
                rows={12}
                maxLength={100000}
                value={values.template_content}
                onChange={(e) => set("template_content", e.target.value)}
              />
              <span className="muted-copy">
                {values.template_content.length.toLocaleString()} / 100,000
              </span>
              <SamplePreview content={values.template_content} />
            </fieldset>
            <aside className="placeholder-panel" aria-label="Placeholder help">
              <h3>Insert Placeholder</h3>
              <p className="muted-copy">插入到光标位置，或替换所选文本。</p>
              {!registry.data ? (
                <QueryState queries={[registry]} />
              ) : (
                registry.data.map((p) => (
                  <div className="placeholder-item" key={p.key}>
                    <small>{p.group}</small>
                    <Button
                      type="button"
                      variant="secondary"
                      disabled={save.isPending}
                      onClick={() => insert(p.key)}
                    >
                      {p.label}
                    </Button>
                    <code>{`{{${p.key}}}`}</code>
                    <p>{p.description}</p>
                    <small>Example: {p.example}</small>
                  </div>
                ))
              )}
            </aside>
          </div>
          {save.error && (
            <p className="error-banner" role="alert">
              {save.error.message}
            </p>
          )}
          <DialogFooter>
            <span role="status">
              {save.isPending
                ? "Saving…"
                : save.isError
                  ? "Save failed"
                  : dirty
                    ? "Unsaved"
                    : id
                      ? "Saved"
                      : "New template"}
            </span>
            <Button
              type="button"
              variant="secondary"
              onClick={close}
              disabled={save.isPending}
            >
              Close
            </Button>
            <Button
              type="submit"
              disabled={
                save.isPending ||
                !dirty ||
                !values.name.trim() ||
                !values.template_content.trim() ||
                (values.scope === "PROJECT" && !values.project_id)
              }
            >
              Save Template
            </Button>
          </DialogFooter>
        </form>
        <Dialog open={discard} onOpenChange={setDiscard}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Unsaved changes</DialogTitle>
              <DialogDescription>
                关闭将丢弃未保存的模板修改。
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="secondary" onClick={() => setDiscard(false)}>
                Stay
              </Button>
              <Button onClick={onClose}>Discard and Close</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </DialogContent>
    </Dialog>
  );
}
