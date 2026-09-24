import { useCallback, useRef, useState } from "react";
import {
  Link,
  useBeforeUnload,
  useBlocker,
  useLocation,
  useNavigate,
  useParams,
} from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Save } from "lucide-react";
import { requestJson, isMissingEntity } from "@/api/client";
import { shotsKeys } from "@/api/query-keys";
import { PageHeader } from "@/components/common/page-header";
import { WorkspacePanel } from "@/components/common/workspace-panel";
import { QueryState, QueryErrors } from "@/components/common/query-state";
import { StatusBadge } from "@/components/common/status-badge";
import { Choice } from "@/components/common/entity-form";
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
import { shotStatusOptions } from "@/lib/status-display";
import type { Scene } from "@/features/scenes/types";
import type { ShotState } from "@/features/characters/types";
import type { Asset } from "@/features/assets/types";
import type { Shot, ShotStatus } from "./types";
import { shotApi } from "./api";
import { WorkspaceCharacters } from "./workspace-characters";
import { WorkspaceReferences } from "./workspace-references";
import "./shot-workspace.css";
import { PromptTemplatePicker } from "@/features/templates/template-picker";

interface Workspace {
  shot: Shot;
  scene: Scene;
  character_states: ShotState[];
  assets: Asset[];
  previous_shot: Shot | null;
  next_shot: Shot | null;
  position: number;
  total: number;
}
const requirements = [
  ["main_action", "Main Action", "当前镜头具体发生什么"],
  ["key_constraints", "Key Constraints", "必须满足的镜头级要求"],
  ["negative_constraints", "Negative Constraints", "明确禁止出现的内容"],
  ["free_notes", "Free Notes", "镜头语言、反馈与其他补充"],
] as const;
function formValues(shot: Shot) {
  return {
    title: shot.title,
    description: shot.description,
    duration_seconds: String(shot.duration_seconds),
    status: shot.status,
    main_action: shot.main_action ?? "",
    key_constraints: shot.key_constraints ?? "",
    negative_constraints: shot.negative_constraints ?? "",
    free_notes: shot.free_notes ?? "",
  };
}
function WorkspaceContent({ data }: { data: Workspace }) {
  const { shot, scene } = data;
  const [values, setValues] = useState(() => formValues(shot));
  const [saved, setSaved] = useState(() => formValues(shot));
  const busy = useRef(false);
  const dirty = JSON.stringify(values) !== JSON.stringify(saved);
  const client = useQueryClient();
  const navigate = useNavigate();
  const location = useLocation();
  const source = (location.state as { returnTo?: string } | null)?.returnTo;
  const returnTo =
    source &&
    ["shots", "script", "scenes"].some(
      (p) => source.split("?")[0] === `/projects/${shot.project_id}/${p}`,
    )
      ? source
      : `/projects/${shot.project_id}/shots`;
  const save = useMutation({
    mutationFn: () =>
      shotApi.update(shot.id, {
        ...values,
        duration_seconds: Number(values.duration_seconds),
      }),
    onSuccess: async (updated) => {
      setValues(formValues(updated));
      setSaved(formValues(updated));
      client.setQueryData(shotsKeys.detail(shot.id), updated);
      await Promise.all([
        client.invalidateQueries({ queryKey: ["shot-workspace", shot.id] }),
        client.invalidateQueries({
          queryKey: shotsKeys.byProject(shot.project_id),
        }),
        client.invalidateQueries({
          queryKey: shotsKeys.byScene(shot.scene_id),
        }),
      ]);
    },
  });
  const blocker = useBlocker(dirty || save.isPending);
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
  const valid =
    values.title.trim() &&
    values.duration_seconds.trim() &&
    Number.isFinite(Number(values.duration_seconds)) &&
    Number(values.duration_seconds) >= 0;
  return (
    <div className="workspace-page shot-workspace">
      <Link className="back-link" to={returnTo}>
        ← 返回镜头列表
      </Link>
      <PageHeader
        title={`${shot.shot_code} · ${shot.title}`}
        description="Shot Workspace"
        metadata={
          <>
            <span>{shot.duration_seconds}s</span>
            <StatusBadge status={shot.status} />
          </>
        }
      />
      <div className="workspace-command-bar">
        <div className="row-actions">
          <Button
            variant="secondary"
            disabled={!data.previous_shot || save.isPending}
            onClick={() =>
              navigate(`/shots/${data.previous_shot!.id}/workspace`, {
                state: { returnTo },
              })
            }
          >
            <ArrowLeft />
            Previous Shot
          </Button>
          <span className="muted-copy">
            {data.position} / {data.total}
          </span>
          <Button
            variant="secondary"
            disabled={!data.next_shot || save.isPending}
            onClick={() =>
              navigate(`/shots/${data.next_shot!.id}/workspace`, {
                state: { returnTo },
              })
            }
          >
            Next Shot
            <ArrowRight />
          </Button>
        </div>
        <div className="row-actions">
          <span role="status">
            {save.isPending
              ? "Saving…"
              : save.isError
                ? "Save failed"
                : dirty
                  ? "Unsaved changes"
                  : "Saved"}
          </span>
          <Button
            type="submit"
            form="shot-requirements"
            disabled={!dirty || !valid || save.isPending}
          >
            <Save />
            {save.isPending ? "Saving…" : "Save Changes"}
          </Button>
        </div>
      </div>
      <PromptTemplatePicker projectId={shot.project_id} />
      <div className="shot-workspace-grid">
        <aside className="workspace-context">
          <WorkspacePanel
            title="Scene Context"
            description="场景事实与长期约束 · 只读"
          >
            <h3>{scene.name}</h3>
            <p>{scene.description || "未填写场景描述"}</p>
            <h4>Fixed Constraints</h4>
            <p>{scene.fixed_constraints || "未填写"}</p>
            <h4>Negative Constraints</h4>
            <p>{scene.negative_constraints || "未填写"}</p>
            <Link
              className="back-link"
              to={`/projects/${shot.project_id}/scenes`}
            >
              Open Scene →
            </Link>
          </WorkspacePanel>
          <WorkspaceCharacters
            shotId={shot.id}
            projectId={shot.project_id}
            linked={data.character_states}
          />
        </aside>
        <WorkspacePanel
          title="Shot Requirements"
          description="当前镜头的动作、限制与生产补充"
          className="workspace-requirements"
        >
          <form
            id="shot-requirements"
            onSubmit={async (event) => {
              event.preventDefault();
              if (!valid || busy.current || !dirty) return;
              busy.current = true;
              try {
                await save.mutateAsync();
              } catch {
                /* Inline mutation error retains the draft. */
              } finally {
                busy.current = false;
              }
            }}
          >
            <fieldset disabled={save.isPending}>
              <label htmlFor="shot-title">Title</label>
              <Input
                id="shot-title"
                required
                maxLength={255}
                value={values.title}
                onChange={(e) => set("title", e.target.value)}
              />
              <label htmlFor="shot-description">Description</label>
              <Textarea
                id="shot-description"
                rows={2}
                value={values.description}
                onChange={(e) => set("description", e.target.value)}
              />
              <div className="workspace-form-pair">
                <div>
                  <label htmlFor="shot-duration">Duration (seconds)</label>
                  <Input
                    id="shot-duration"
                    type="number"
                    min={0}
                    step="any"
                    required
                    value={values.duration_seconds}
                    onChange={(e) => set("duration_seconds", e.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor="shot-status">Production Status</label>
                  <Choice
                    id="shot-status"
                    label="Production Status"
                    value={values.status}
                    onChange={(v) => set("status", v as ShotStatus)}
                    options={shotStatusOptions}
                    disabled={save.isPending}
                  />
                </div>
              </div>
              {requirements.map(([key, label, hint]) => (
                <div className="workspace-requirement-field" key={key}>
                  <label htmlFor={key}>{label}</label>
                  <span className="muted-copy">{hint}</span>
                  <Textarea
                    id={key}
                    rows={key === "main_action" ? 5 : 3}
                    value={values[key]}
                    onChange={(e) => set(key, e.target.value)}
                  />
                </div>
              ))}
            </fieldset>
            {save.error && (
              <p className="error-banner" role="alert">
                {save.error.message} · 修改仍保留，请重试。
              </p>
            )}
          </form>
          {shot.creative_requirement && (
            <details className="workspace-legacy">
              <summary>Legacy Creative Requirement</summary>
              <p>{shot.creative_requirement}</p>
              <Link className="back-link" to={`/shots/${shot.id}`}>
                打开原镜头详情编辑 →
              </Link>
            </details>
          )}
        </WorkspacePanel>
        <div className="workspace-references">
          <WorkspaceReferences shotId={shot.id} assets={data.assets} />
        </div>
      </div>
      <WorkspacePanel
        title="Production Status"
        metadata={<StatusBadge status={shot.status} />}
        description="基于已保存数据；角色与资产绑定即时保存，镜头字段使用 Save Changes。"
      >
        <dl className="workspace-readiness">
          <div>
            <dt>Scene</dt>
            <dd>Ready</dd>
          </div>
          <div>
            <dt>Characters</dt>
            <dd>
              {data.character_states.length
                ? `${data.character_states.length} assigned`
                : "Not assigned"}
            </dd>
          </div>
          <div>
            <dt>References</dt>
            <dd>{data.assets.length} assets</dd>
          </div>
          <div>
            <dt>Main Action</dt>
            <dd>{shot.main_action?.trim() ? "Ready" : "Not set"}</dd>
          </div>
        </dl>
      </WorkspacePanel>
      <Dialog
        open={blocker.state === "blocked"}
        onOpenChange={(open) => {
          if (!open && blocker.state === "blocked" && !save.isPending)
            blocker.reset();
        }}
      >
        <DialogContent closeDisabled={save.isPending}>
          <DialogHeader>
            <DialogTitle>Unsaved changes</DialogTitle>
            <DialogDescription>
              {save.isPending
                ? "正在保存，请稍候。"
                : "离开将丢弃未保存的镜头修改。留在此页可继续编辑或保存。"}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="secondary"
              disabled={save.isPending}
              onClick={() => blocker.state === "blocked" && blocker.reset()}
            >
              Stay
            </Button>
            <Button
              disabled={save.isPending}
              onClick={() => blocker.state === "blocked" && blocker.proceed()}
            >
              Discard and Leave
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
export function Component() {
  const { shotId = "" } = useParams();
  const query = useQuery({
    queryKey: ["shot-workspace", shotId],
    // Each visit starts from persisted context; an old cached form must not
    // overwrite edits made through Shot Detail while this workspace was closed.
    gcTime: 0,
    queryFn: () => requestJson<Workspace>(`/shots/${shotId}/workspace`),
  });
  if (!query.data || isMissingEntity(query.error))
    return <QueryState queries={[query]} />;
  return (
    <>
      <QueryErrors queries={[query]} />
      <WorkspaceContent key={shotId} data={query.data} />
    </>
  );
}
