import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Upload, Eye, Check, Image } from "lucide-react";
import { WorkspacePanel } from "@/components/common/workspace-panel";
import { QueryErrors, QueryState } from "@/components/common/query-state";
import { Choice, DeleteEntity } from "@/components/common/entity-form";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { AssetPicker } from "@/features/assets/asset-picker";
import { AssetDetailSheet } from "@/features/assets/asset-detail";
import { assetApi } from "@/features/assets/api";
import { promptApi } from "@/features/prompts/api";
import { storyboardApi, type Storyboard } from "./api";
import "./storyboards.css";

function Source({ record }: { record: Storyboard }) {
  const source = record.source_prompt;
  return (
    <span className="muted-copy">
      {source
        ? `Source Prompt V${source.version} · ${source.prompt_type}${source.is_edited ? " · Edited" : ""}`
        : "Source Prompt · 未关联"}
    </span>
  );
}

export function StoryboardPanel({
  shotId,
  onBusyChange,
}: {
  shotId: string;
  onBusyChange: (busy: boolean) => void;
}) {
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["storyboards", shotId],
    queryFn: () => storyboardApi.history(shotId),
  });
  const prompts = useQuery({
    queryKey: ["prompt-history", shotId],
    queryFn: () => promptApi.history(shotId),
  });
  const [source, setSource] = useState("selected");
  const [notes, setNotes] = useState("");
  const [view, setView] = useState<Storyboard>();
  const [assetId, setAssetId] = useState("");
  const [dragging, setDragging] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const busy = useRef(false);
  const selectedPrompt = prompts.data?.find(
    (p) => p.prompt_type === "STORYBOARD_6GRID" && p.is_selected,
  );
  const sourceId =
    source === "none"
      ? null
      : source === "selected"
        ? (selectedPrompt?.id ?? null)
        : source;
  const action = useMutation({
    mutationFn: (fn: () => Promise<unknown>) => fn(),
    onSuccess: async () => {
      await Promise.all([
        client.invalidateQueries({ queryKey: ["storyboards", shotId] }),
        client.invalidateQueries({ queryKey: ["shot-workspace", shotId] }),
        client.invalidateQueries({ queryKey: ["assets"] }),
      ]);
    },
  });
  useEffect(() => {
    onBusyChange(action.isPending);
    return () => onBusyChange(false);
  }, [action.isPending, onBusyChange]);
  async function run(fn: () => Promise<unknown>) {
    if (busy.current) return;
    busy.current = true;
    try {
      await action.mutateAsync(fn);
    } finally {
      busy.current = false;
    }
  }
  async function upload(file?: File) {
    if (!file || busy.current) return;
    setDragging(false);
    try {
      await run(async () => {
        if (file.size > 512 * 1024 * 1024)
          throw new Error("单个文件不能超过 512 MiB。");
        await storyboardApi.upload(shotId, file, sourceId, notes);
      });
    } catch {
      /* The mutation displays an actionable inline error. */
    } finally {
      if (input.current) input.current.value = "";
    }
  }
  const records = query.data ?? [];
  const selected = records.find((r) => r.is_selected);
  const unavailable = action.isPending || prompts.isPending || prompts.isError;
  return (
    <WorkspacePanel
      title="Storyboard"
      description="外部生成的六宫格 · 每次导入创建新版本并采用"
      className="storyboard-panel"
    >
      <div
        className={`storyboard-import ${dragging ? "is-dragging" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          if (!unavailable) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          if (!unavailable) void upload(e.dataTransfer.files[0]);
        }}
      >
        <Choice
          label="Storyboard source Prompt"
          value={source}
          onChange={setSource}
          disabled={unavailable}
          options={[
            {
              value: "selected",
              label: selectedPrompt
                ? `Selected 六宫格 Prompt V${selectedPrompt.version}`
                : "无 Selected 六宫格 Prompt · 不关联来源",
            },
            { value: "none", label: "不关联来源 Prompt" },
            ...(prompts.data ?? []).map((p) => ({
              value: p.id,
              label: `${p.prompt_type} · V${p.version}${p.is_selected ? " · Selected" : ""}`,
            })),
          ]}
        />
        <Textarea
          aria-label="Storyboard notes"
          placeholder="本次导入备注（可选）"
          rows={2}
          maxLength={10000}
          value={notes}
          disabled={action.isPending}
          onChange={(e) => setNotes(e.target.value)}
        />
        <div className="row-actions">
          <Button disabled={unavailable} onClick={() => input.current?.click()}>
            <Upload />
            {action.isPending ? "Saving…" : "Import New Storyboard"}
          </Button>
          <AssetPicker
            bound={[]}
            assetType="STORYBOARD_6GRID"
            label="Use Existing Asset"
            disabled={unavailable}
            onConfirm={(id) =>
              run(() => storyboardApi.create(shotId, id, sourceId, notes))
            }
          />
          <span className="muted-copy">
            拖入一张 PNG / JPEG / WebP · 最多 512 MiB
          </span>
          <input
            className="sr-only"
            ref={input}
            type="file"
            accept=".png,.jpg,.jpeg,.webp"
            aria-label="Import storyboard image"
            disabled={unavailable}
            onChange={(e) => void upload(e.target.files?.[0])}
          />
        </div>
      </div>
      <QueryErrors queries={[prompts, query]} />
      {action.error && (
        <p role="alert" className="error-banner">
          {action.error.message} · 请检查后重新操作。
        </p>
      )}
      {!query.data ? (
        <QueryState queries={[query]} />
      ) : (
        <>
          <h3>Current Selected</h3>
          {selected ? (
            <div className="storyboard-current">
              <button
                onClick={() => setView(selected)}
                aria-label={`View selected Storyboard V${selected.version}`}
              >
                <img
                  src={assetApi.thumbnail(selected.asset_id)}
                  alt={`Selected storyboard V${selected.version}`}
                  loading="lazy"
                />
              </button>
              <div>
                <strong>
                  V{selected.version} · {selected.asset.name}
                </strong>
                <Source record={selected} />
                <p>{new Date(selected.created_at).toLocaleString()}</p>
              </div>
            </div>
          ) : (
            <p className="muted-copy">
              {records.length
                ? "No selected storyboard · 从历史选择一个版本"
                : "No storyboards yet · 导入外部生成的六宫格"}
            </p>
          )}
          <h3>
            History{" "}
            <span className="muted-copy">{records.length} versions</span>
          </h3>
          <div className="storyboard-history">
            {records.map((r) => (
              <article
                key={r.id}
                aria-label={`Storyboard V${r.version}`}
                className="storyboard-row"
              >
                <img
                  src={assetApi.thumbnail(r.asset_id)}
                  alt={`Storyboard V${r.version} thumbnail`}
                  loading="lazy"
                />
                <div className="storyboard-meta">
                  <strong>
                    V{r.version} · {r.asset.name}
                  </strong>
                  <Source record={r} />
                  <span className="muted-copy">
                    {new Date(r.created_at).toLocaleString()}
                  </span>
                  {r.notes && <p>{r.notes}</p>}
                  {r.is_selected && <Badge tone="success">Selected</Badge>}
                </div>
                <div className="row-actions">
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={r.is_selected || action.isPending}
                    onClick={() =>
                      void run(() => storyboardApi.select(r.id)).catch(() => {})
                    }
                  >
                    <Check />
                    Select
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setView(r)}>
                    <Eye />
                    View
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setAssetId(r.asset_id)}
                  >
                    <Image />
                    Open Asset
                  </Button>
                  <DeleteEntity
                    name={`Storyboard V${r.version}`}
                    description="仅软删除此分镜版本；参考绑定、Asset 和文件均保留。删除当前采用版本后不自动选择其他版本。"
                    onDelete={() => run(() => storyboardApi.remove(r.id))}
                  />
                </div>
              </article>
            ))}
          </div>
        </>
      )}
      <Dialog
        open={Boolean(view)}
        onOpenChange={(open) => {
          if (!open) setView(undefined);
        }}
      >
        <DialogContent className="storyboard-preview">
          <DialogHeader>
            <DialogTitle>Storyboard V{view?.version}</DialogTitle>
            <DialogDescription>
              {view && <Source record={view} />}
            </DialogDescription>
          </DialogHeader>
          {view && (
            <>
              <img
                src={assetApi.file(view.asset_id)}
                alt={`Storyboard V${view.version} original`}
              />
              <p>{view.notes}</p>
              <p className="muted-copy">
                {view.asset.width} × {view.asset.height} ·{" "}
                {new Date(view.created_at).toLocaleString()}
              </p>
            </>
          )}
        </DialogContent>
      </Dialog>
      {assetId && (
        <AssetDetailSheet id={assetId} onClose={() => setAssetId("")} />
      )}
    </WorkspacePanel>
  );
}
