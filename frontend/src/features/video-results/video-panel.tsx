import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Play, RotateCcw, Upload } from "lucide-react";
import { WorkspacePanel } from "@/components/common/workspace-panel";
import { Choice, DeleteEntity } from "@/components/common/entity-form";
import { QueryErrors, QueryState } from "@/components/common/query-state";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { AssetPicker } from "@/features/assets/asset-picker";
import { AssetDetailSheet } from "@/features/assets/asset-detail";
import { assetApi } from "@/features/assets/api";
import { promptApi } from "@/features/prompts/api";
import { storyboardApi } from "@/features/storyboards/api";
import { videoApi, type VideoResult } from "./api";
import "./videos.css";

function Sources({ record }: { record: VideoResult }) {
  return <div className="muted-copy">
    <div>{record.source_storyboard ? `Source Storyboard V${record.source_storyboard.version}${record.source_storyboard.is_deleted ? " · Deleted" : ""}` : "Source Storyboard · 未关联"}</div>
    <div>{record.source_prompt ? `Source Prompt V${record.source_prompt.version} · ${record.source_prompt.prompt_type}${record.source_prompt.is_edited ? " · Edited" : ""}` : "Source Prompt · 未关联"}</div>
  </div>;
}

export function VideoPanel({ shotId, onBusyChange }: { shotId: string; onBusyChange: (busy: boolean) => void }) {
  const client = useQueryClient();
  const query = useQuery({ queryKey: ["video-results", shotId], queryFn: () => videoApi.history(shotId) });
  const storyboards = useQuery({ queryKey: ["storyboards", shotId], queryFn: () => storyboardApi.history(shotId) });
  const prompts = useQuery({ queryKey: ["prompt-history", shotId], queryFn: () => promptApi.history(shotId) });
  const [storyboardId, setStoryboardId] = useState("none");
  const [promptId, setPromptId] = useState("none");
  const [notes, setNotes] = useState("");
  const [showDeleted, setShowDeleted] = useState(false);
  const [view, setView] = useState<VideoResult>();
  const [assetId, setAssetId] = useState("");
  const [playbackFailed, setPlaybackFailed] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const busy = useRef(false);
  const action = useMutation({
    mutationFn: (fn: () => Promise<unknown>) => fn(),
    onSuccess: async () => {
      await Promise.all([
        client.invalidateQueries({ queryKey: ["video-results", shotId] }),
        client.invalidateQueries({ queryKey: ["shot-workspace", shotId] }),
        client.invalidateQueries({ queryKey: ["assets"] }),
      ]);
    },
  });
  useEffect(() => { onBusyChange(action.isPending); return () => onBusyChange(false); }, [action.isPending, onBusyChange]);
  async function run(fn: () => Promise<unknown>) {
    if (busy.current) return;
    busy.current = true;
    try { await action.mutateAsync(fn); } finally { busy.current = false; }
  }
  const sources = { source_storyboard_id: storyboardId === "none" ? null : storyboardId, source_prompt_record_id: promptId === "none" ? null : promptId, notes: notes || null };
  async function upload(file?: File) {
    if (!file || busy.current) return;
    try { await run(async () => {
      if (file.size > 512 * 1024 * 1024) throw new Error("单个文件不能超过 512 MiB。");
      await videoApi.upload(shotId, file, sources);
    }); } catch { /* Mutation error stays visible for explicit retry. */ }
    finally { if (input.current) input.current.value = ""; }
  }
  const records = query.data ?? [];
  const selected = records.find((r) => r.is_selected && !r.deleted_at);
  const unavailable = action.isPending || storyboards.isPending || prompts.isPending || storyboards.isError || prompts.isError;
  function preview(record: VideoResult) { setPlaybackFailed(false); setView(record); }
  return <WorkspacePanel title="Video Results" description="外部视频结果 · 每次导入创建新版本并采用" className="video-results-panel">
    <div className="video-import" onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); if (!unavailable) void upload(e.dataTransfer.files[0]); }}>
      <div className="video-sources">
        <Choice label="Video source Storyboard" value={storyboardId} onChange={setStoryboardId} disabled={unavailable} options={[{ value: "none", label: "不关联来源 Storyboard" }, ...(storyboards.data ?? []).map((s) => ({ value: s.id, label: `Storyboard V${s.version}${s.is_selected ? " · Selected" : ""}` }))]} />
        <Choice label="Video source Prompt" value={promptId} onChange={setPromptId} disabled={unavailable} options={[{ value: "none", label: "不关联来源 Prompt" }, ...(prompts.data ?? []).map((p) => ({ value: p.id, label: `${p.prompt_type} · V${p.version}${p.is_selected ? " · Selected" : ""}` }))]} />
      </div>
      <Textarea aria-label="Video notes" placeholder="本次视频备注（可选）" rows={2} maxLength={10000} value={notes} disabled={action.isPending} onChange={(e) => setNotes(e.target.value)} />
      <div className="row-actions">
        <Button disabled={unavailable} onClick={() => input.current?.click()}><Upload />Import Video</Button>
        <AssetPicker bound={[]} assetType="VIDEO" label="Use Existing Video Asset" disabled={unavailable} onConfirm={(id) => run(() => videoApi.create(shotId, id, sources))} />
        <span className="muted-copy">拖入 MP4 / MOV / WebM · 最多 512 MiB</span>
        <input ref={input} className="sr-only" type="file" accept=".mp4,.mov,.webm" aria-label="Import video file" disabled={unavailable} onChange={(e) => void upload(e.target.files?.[0])} />
      </div>
    </div>
    <QueryErrors queries={[query, storyboards, prompts]} />
    {action.error && <p role="alert" className="error-banner">{action.error.message} · 请检查后重新操作。</p>}
    {!query.data ? <QueryState queries={[query]} /> : <>
      <h3>Current Selected</h3>
      {selected ? <div className="video-current"><Button variant="secondary" onClick={() => preview(selected)}><Play />Preview Video V{selected.version}</Button><Sources record={selected} /></div> : <p className="muted-copy">No selected video · 导入或从历史选择一个版本</p>}
      <div className="video-history-heading"><h3>History</h3><label><input type="checkbox" checked={showDeleted} onChange={(e) => setShowDeleted(e.target.checked)} /> Show deleted videos</label></div>
      {records.filter((r) => showDeleted || !r.deleted_at).map((r) => <article key={r.id} aria-label={`Video V${r.version}`} className="video-result-row">
        {!r.deleted_at && <img src={assetApi.thumbnail(r.asset_id)} alt={`Video V${r.version} thumbnail`} loading="lazy" />}
        <div className="video-result-meta"><strong>V{r.version} · {r.asset.name}</strong><Sources record={r} /><span className="muted-copy">{new Date(r.created_at).toLocaleString()}</span>{r.notes && <p>{r.notes}</p>}{r.is_selected && <Badge tone="success">Selected</Badge>}{r.deleted_at && <Badge>Deleted</Badge>}</div>
        <div className="row-actions">{r.deleted_at ? <Button size="sm" variant="secondary" disabled={action.isPending} onClick={() => void run(() => videoApi.restore(r.id)).catch(() => {})}><RotateCcw />Restore</Button> : <>
          <Button size="sm" variant="secondary" disabled={r.is_selected || action.isPending} onClick={() => void run(() => videoApi.select(r.id)).catch(() => {})}><Check />Select</Button>
          <Button size="sm" variant="ghost" onClick={() => preview(r)}><Play />Preview</Button>
          <Button size="sm" variant="ghost" onClick={() => setAssetId(r.asset_id)}>Open Asset</Button>
          <DeleteEntity name={`Video V${r.version}`} description="仅软删除此视频版本；Asset、文件和参考绑定保留。删除当前采用版本后不自动选择其他版本。" onDelete={() => run(() => videoApi.remove(r.id))} />
        </>}</div>
      </article>)}
    </>}
    <Dialog open={Boolean(view)} onOpenChange={(open) => { if (!open) setView(undefined); }}>
      <DialogContent className="video-preview"><DialogHeader><DialogTitle>Video V{view?.version}</DialogTitle><DialogDescription>点击播放查看此版本的原始视频</DialogDescription></DialogHeader>
        {view && <><video aria-label={`Video V${view.version} playback`} controls preload="metadata" poster={assetApi.thumbnail(view.asset_id)} src={assetApi.file(view.asset_id)} onError={() => setPlaybackFailed(true)} /><Sources record={view} /><p>{view.notes}</p>{playbackFailed && <p role="alert">当前浏览器无法播放此视频。<a href={assetApi.file(view.asset_id)} download={view.asset.original_filename}>打开原文件</a></p>}</>}
      </DialogContent>
    </Dialog>
    {assetId && <AssetDetailSheet id={assetId} onClose={() => setAssetId("")} />}
  </WorkspacePanel>;
}
