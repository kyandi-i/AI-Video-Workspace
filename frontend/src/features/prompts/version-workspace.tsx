import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, Pencil, RotateCw, Save, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { QueryState } from "@/components/common/query-state";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { categories } from "@/features/templates/api";
import { promptApi, type PromptRecord } from "./api";

export function VersionWorkspace({
  initial,
  contextDirty,
  onProtectedChange,
}: {
  initial: PromptRecord;
  contextDirty: boolean;
  onProtectedChange: (value: boolean) => void;
}) {
  const client = useQueryClient();
  const history = useQuery({
    queryKey: ["prompt-history", initial.shot_id],
    queryFn: () => promptApi.history(initial.shot_id),
  });
  const [viewed, setViewed] = useState<string>();
  const [dirty, setDirty] = useState(false);
  const [pendingView, setPendingView] = useState<string>();
  const records = history.data ?? [initial];
  const record =
    records.find((r) => r.id === viewed) ??
    records.find(
      (r) => r.is_selected && r.prompt_type === initial.prompt_type,
    ) ??
    initial;
  const selected = records.find(
    (r) => r.is_selected && r.prompt_type === record.prompt_type,
  );
  const [copyStatus, setCopyStatus] = useState("");
  const changed = async (updated: PromptRecord) => {
    setViewed(updated.id);
    await Promise.all([
      client.invalidateQueries({
        queryKey: ["prompt-history", initial.shot_id],
      }),
      client.invalidateQueries({
        queryKey: ["prompt-result", initial.shot_id],
      }),
    ]);
  };
  return (
    <div className="space-y-4">
      <div className="row-actions">
        <h3>Version History</h3>
        {selected && (
          <Button
            variant="secondary"
            onClick={async () => {
              try {
                await navigator.clipboard.writeText(selected.effective_content);
                setCopyStatus("Selected Prompt copied");
              } catch {
                setCopyStatus("复制失败，请选择文本手动复制。");
              }
            }}
          >
            <Copy />
            Copy Selected Prompt
          </Button>
        )}
        <span role="status">{copyStatus}</span>
      </div>
      {(history.isPending || history.error) && (
        <QueryState queries={[history]} />
      )}
      <div className="prompt-history" aria-label="Version History">
        {records.map((r) => (
          <button
            type="button"
            key={r.id}
            aria-pressed={r.id === record.id}
            aria-label={`View V${r.version} ${r.template_name}`}
            onClick={() => {
              if (r.id === record.id) return;
              if (dirty) setPendingView(r.id);
              else setViewed(r.id);
            }}
          >
            <strong>V{r.version}</strong>{" "}
            <span>
              {categories.find((o) => o.value === r.prompt_type)?.label ??
                "Other"}{" "}
              · {r.template_name}
            </span>
            {r.is_selected && <Badge>Selected</Badge>}
            {r.edited_content !== null && <Badge>Edited</Badge>}
            <small>
              {r.provider} / {r.model_name} ·{" "}
              {new Date(r.created_at).toLocaleString()}
            </small>
          </button>
        ))}
      </div>
      <VersionEditor
        key={record.id}
        record={record}
        contextDirty={contextDirty}
        onChange={changed}
        onProtectedChange={onProtectedChange}
        onDirtyChange={setDirty}
      />
      <Dialog
        open={Boolean(pendingView)}
        onOpenChange={(open) => {
          if (!open) setPendingView(undefined);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Unsaved changes</DialogTitle>
            <DialogDescription>
              切换版本将丢弃未保存的 Prompt 修改。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="secondary"
              onClick={() => setPendingView(undefined)}
            >
              Stay
            </Button>
            <Button
              onClick={() => {
                setViewed(pendingView);
                setPendingView(undefined);
              }}
            >
              Discard and Switch
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function VersionEditor({
  record,
  contextDirty,
  onChange,
  onProtectedChange,
  onDirtyChange,
}: {
  record: PromptRecord;
  contextDirty: boolean;
  onChange: (record: PromptRecord) => Promise<void>;
  onProtectedChange: (value: boolean) => void;
  onDirtyChange: (value: boolean) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(record.effective_content);
  const [saved, setSaved] = useState(record.effective_content);
  const [copyStatus, setCopyStatus] = useState("");
  const operation = useRef<{ id: string; hash: string } | undefined>(undefined);
  const busy = useRef(false);
  const dirty = editing && draft !== saved;
  const save = useMutation({
    mutationFn: () => promptApi.edit(record.id, draft),
    onSuccess: async (r) => {
      setSaved(r.effective_content);
      setEditing(false);
      await onChange(r);
    },
  });
  const select = useMutation({
    mutationFn: () => promptApi.select(record.id),
    onSuccess: onChange,
  });
  const regenerate = useMutation({
    mutationFn: async () => {
      const preview = await promptApi.preview(
        record.shot_id,
        record.template_id,
      );
      if (!operation.current || operation.current.hash !== preview.input_hash)
        operation.current = {
          id: crypto.randomUUID(),
          hash: preview.input_hash,
        };
      return promptApi.regenerate(
        record.id,
        preview.input_hash,
        operation.current.id,
      );
    },
    onSuccess: async (r) => {
      operation.current = undefined;
      await onChange(r);
    },
  });
  const pending = save.isPending || select.isPending || regenerate.isPending;
  useEffect(() => {
    onProtectedChange(dirty || pending);
    onDirtyChange(dirty || pending);
    return () => {
      onProtectedChange(false);
      onDirtyChange(false);
    };
  }, [dirty, pending, onProtectedChange, onDirtyChange]);
  const run = async (action: () => Promise<unknown>) => {
    if (busy.current) return;
    busy.current = true;
    try {
      await action();
    } catch {
      /* Preserve draft and operation for explicit retry. */
    } finally {
      busy.current = false;
    }
  };
  return (
    <div className="prompt-result">
      <div className="row-actions">
        <h3>Generated Prompt · V{record.version}</h3>
        {record.is_selected && <Badge>Selected</Badge>}
        {record.edited_content !== null && <Badge>Edited</Badge>}
        <Button
          variant="secondary"
          onClick={async () => {
            try {
              await navigator.clipboard.writeText(record.effective_content);
              setCopyStatus("Copied");
            } catch {
              setCopyStatus("复制失败，请选择文本手动复制。");
            }
          }}
        >
          <Copy />
          Copy Prompt
        </Button>
        <span role="status">{copyStatus}</span>
      </div>
      <p className="muted-copy">
        {record.template_name} · {record.provider} / {record.model_name} ·{" "}
        {new Date(record.created_at).toLocaleString()}
      </p>
      {editing ? (
        <>
          <label htmlFor="prompt-edit">Edit Prompt</label>
          <Textarea
            id="prompt-edit"
            rows={10}
            maxLength={500000}
            disabled={pending}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
          />
          <div className="row-actions">
            <Button
              disabled={!dirty || pending}
              onClick={() => void run(() => save.mutateAsync())}
            >
              <Save />
              {save.isPending ? "Saving Prompt…" : "Save Prompt"}
            </Button>
            <Button
              variant="secondary"
              disabled={pending}
              onClick={() => {
                setDraft(saved);
                setEditing(false);
              }}
            >
              Cancel Edit
            </Button>
            <span role="status">
              {dirty ? "Unsaved Prompt changes" : "Saved"}
            </span>
          </div>
        </>
      ) : (
        <pre tabIndex={0} aria-label="Generated Prompt result">
          {record.effective_content}
        </pre>
      )}
      <div className="row-actions">
        {!editing && (
          <Button
            variant="secondary"
            disabled={pending}
            onClick={() => {
              setDraft(record.effective_content);
              setSaved(record.effective_content);
              setEditing(true);
            }}
          >
            <Pencil />
            Edit Prompt
          </Button>
        )}
        <Button
          variant="secondary"
          disabled={record.is_selected || dirty || pending}
          onClick={() => void run(() => select.mutateAsync())}
        >
          <Check />
          {select.isPending
            ? "Selecting…"
            : record.is_selected
              ? "Selected"
              : "Select Prompt"}
        </Button>
        <Button
          disabled={dirty || pending || contextDirty}
          onClick={() => void run(() => regenerate.mutateAsync())}
        >
          <RotateCw />
          {regenerate.isPending
            ? "Regenerating…"
            : regenerate.isError
              ? "Retry Regeneration"
              : "Regenerate"}
        </Button>
      </div>
      <p className="muted-copy">
        Regenerate
        使用此版本的来源模板与已保存的最新镜头上下文；成功后采用新版本。Copy
        复制已保存内容。
      </p>
      {[save.error, select.error, regenerate.error]
        .filter(Boolean)
        .map((e, i) => (
          <p key={i} role="alert" className="error-banner">
            {e!.message}
          </p>
        ))}
      <details>
        <summary>本次生成使用的输入</summary>
        <pre>{record.rendered_input}</pre>
      </details>
      <details className="prompt-facts">
        <summary>Generation facts</summary>
        <p>Original output</p>
        <p className="prompt-fact-text">{record.generated_content}</p>
        <p>Template snapshot</p>
        <p className="prompt-fact-text">{record.template_content}</p>
        <p>Context snapshot</p>
        <p className="prompt-fact-text">{record.context_json.shot_context}</p>
      </details>
    </div>
  );
}
