import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { DetailSheet } from "@/components/common/detail-sheet";
import {
  EntityForm,
  DeleteEntity,
  Choice,
} from "@/components/common/entity-form";
import { QueryState, QueryErrors } from "@/components/common/query-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useProjects } from "@/features/projects/hooks";
import { notify } from "@/lib/notifications";
import { isMissingEntity } from "@/api/client";
import { useAsset, useAssetActions, useBindingShots } from "./hooks";
import { assetApi } from "./api";
import {
  assetDisplay,
  assetTypeOptions,
  dimensions,
  sizeLabel,
} from "./display";
import type { AssetDetail, AssetType } from "./types";

function Content({ asset, close }: { asset: AssetDetail; close: () => void }) {
  const actions = useAssetActions(asset.id);
  const projects = useProjects();
  const [projectId, setProjectId] = useState("");
  const [shotId, setShotId] = useState("");
  const [tag, setTag] = useState("");
  const shots = useBindingShots(projectId);
  const busy = useRef(false);
  async function run(action: () => Promise<unknown>, done?: () => void) {
    if (busy.current) return;
    busy.current = true;
    try {
      await action();
      done?.();
      notify.success("已更新资产");
    } catch (error) {
      notify.error(
        error instanceof Error ? error.message : "操作失败，请重试。",
      );
    } finally {
      busy.current = false;
    }
  }
  return (
    <div className="asset-detail-content">
      <div className="asset-detail-actions">
        <EntityForm
          title="编辑资产"
          trigger={<Button variant="secondary">编辑资产</Button>}
          fields={[
            { name: "name", label: "名称", required: true, maxLength: 255 },
            { name: "description", label: "描述", kind: "textarea" },
            {
              name: "asset_type",
              label: "资产类型",
              kind: "select",
              options: assetTypeOptions.filter(
                (option) =>
                  option.value === "OTHER" ||
                  (asset.mime_type.startsWith("video/")
                    ? option.value === "VIDEO"
                    : option.value !== "VIDEO"),
              ),
            },
          ]}
          initial={{
            name: asset.name,
            description: asset.description,
            asset_type: asset.asset_type,
          }}
          onSave={(values) =>
            actions.save({
              name: values.name,
              description: values.description,
              asset_type: values.asset_type as AssetType,
            })
          }
        />
        <DeleteEntity
          name={asset.name}
          description={
            asset.projects.length +
              asset.shots.length +
              asset.characters.length +
              asset.character_states.length >
            0
              ? `仍有 ${asset.projects.length} 个项目、${asset.shots.length} 个镜头、${asset.characters.length} 个角色、${asset.character_states.length} 个状态引用，请先解除绑定。`
              : "原文件与缩略图会保留，不会永久删除。"
          }
          onDelete={async () => {
            await actions.remove();
            close();
          }}
        />
      </div>
      <p className="asset-description">{asset.description || "未填写描述"}</p>
      <dl className="asset-facts">
        <dt>资产类型</dt>
        <dd>
          <Badge tone={assetDisplay[asset.asset_type].tone}>
            {assetDisplay[asset.asset_type].label}
          </Badge>
        </dd>
        <dt>原始文件名</dt>
        <dd>{asset.original_filename}</dd>
        <dt>文件大小</dt>
        <dd>{sizeLabel(asset.file_size)}</dd>
        <dt>MIME</dt>
        <dd>{asset.mime_type}</dd>
        <dt>尺寸 / 时长</dt>
        <dd>{dimensions(asset)}</dd>
        <dt>创建时间</dt>
        <dd>{new Date(asset.created_at).toLocaleString()}</dd>
        <dt>更新时间</dt>
        <dd>{new Date(asset.updated_at).toLocaleString()}</dd>
      </dl>
      <section className="asset-detail-section">
        <h3>Characters / States using this asset</h3>
        {!asset.characters.length && !asset.character_states.length && (
          <p>尚无角色引用</p>
        )}
        {asset.characters.map((item) => (
          <Link
            className="back-link"
            key={item.id}
            to={`/projects/${item.project_id}/characters/${item.id}`}
          >
            {item.name} →
          </Link>
        ))}
        {asset.character_states.map((item) => (
          <p key={item.id}>State: {item.name}（请在角色详情解除绑定）</p>
        ))}
      </section>
      <section className="asset-detail-section">
        <h3>Tags</h3>
        <div className="asset-tags">
          {asset.tags.length ? (
            asset.tags.map((item) => (
              <span key={item.id} className="asset-tag" title={item.name}>
                <span>{item.name}</span>
                <Button
                  size="icon"
                  variant="ghost"
                  aria-label={`移除标签 ${item.name}`}
                  disabled={actions.isPending}
                  onClick={() => void run(() => actions.removeTag(item.id))}
                >
                  ×
                </Button>
              </span>
            ))
          ) : (
            <p>尚无标签</p>
          )}
        </div>
        <form
          className="asset-inline-form"
          onSubmit={(event) => {
            event.preventDefault();
            if (tag.trim())
              void run(
                () => actions.addTag(tag.trim()),
                () => setTag(""),
              );
          }}
        >
          <Input
            aria-label="新标签"
            placeholder="添加标签…"
            maxLength={80}
            value={tag}
            disabled={actions.isPending}
            onChange={(event) => setTag(event.target.value)}
          />
          <Button
            variant="secondary"
            disabled={!tag.trim() || actions.isPending}
          >
            添加标签
          </Button>
        </form>
      </section>
      <section className="asset-detail-section">
        <h3>Projects using this asset</h3>
        <ul className="asset-relations">
          {asset.projects.map((project) => (
            <li key={project.id}>
              <span title={project.name}>
                {project.deleted_at ? (
                  `${project.name}（已删除）`
                ) : (
                  <Link to={`/projects/${project.id}`}>{project.name}</Link>
                )}
              </span>
              <Button
                size="sm"
                variant="ghost"
                disabled={actions.isPending}
                onClick={() =>
                  void run(() => actions.bind("projects", project.id, true))
                }
              >
                解除项目绑定
              </Button>
            </li>
          ))}
        </ul>
        {!asset.projects.length && <p>尚未绑定项目</p>}
        {!projects.data ? (
          <QueryState queries={[projects]} />
        ) : (
          <>
            <QueryErrors queries={[projects]} />
            <div className="asset-inline-form">
              <Choice
                label="绑定项目"
                value={projectId}
                onChange={(value) => {
                  setProjectId(value);
                  setShotId("");
                }}
                disabled={actions.isPending}
                options={projects.data.map((project) => ({
                  value: project.id,
                  label: project.name,
                }))}
              />
              <Button
                variant="secondary"
                disabled={
                  !projectId ||
                  actions.isPending ||
                  asset.projects.some((p) => p.id === projectId)
                }
                onClick={() =>
                  void run(() => actions.bind("projects", projectId))
                }
              >
                绑定项目
              </Button>
            </div>
          </>
        )}
      </section>
      <section className="asset-detail-section">
        <h3>Shots using this asset</h3>
        <ul className="asset-relations">
          {asset.shots.map((shot) => (
            <li key={shot.id}>
              <span title={`${shot.shot_code} · ${shot.title}`}>
                {shot.deleted_at ? (
                  `${shot.shot_code}（已删除）`
                ) : (
                  <Link to={`/shots/${shot.id}`}>
                    {shot.shot_code} · {shot.title}
                  </Link>
                )}
              </span>
              <Button
                size="sm"
                variant="ghost"
                disabled={actions.isPending}
                onClick={() =>
                  void run(() => actions.bind("shots", shot.id, true))
                }
              >
                解除镜头绑定
              </Button>
            </li>
          ))}
        </ul>
        {!asset.shots.length && <p>尚未绑定镜头</p>}
        {!projectId ? (
          <p>先在上方选择项目，再选择该项目的镜头。</p>
        ) : !shots.data ? (
          <QueryState queries={[shots]} />
        ) : (
          <>
            <QueryErrors queries={[shots]} />
            <div className="asset-inline-form">
              <Choice
                label="绑定镜头"
                value={shotId}
                onChange={setShotId}
                disabled={actions.isPending || !shots.data.length}
                options={shots.data.map((shot) => ({
                  value: shot.id,
                  label: `${shot.shot_code} · ${shot.title}`,
                }))}
              />
              <Button
                variant="secondary"
                disabled={
                  !shotId ||
                  actions.isPending ||
                  asset.shots.some((s) => s.id === shotId)
                }
                onClick={() => void run(() => actions.bind("shots", shotId))}
              >
                绑定镜头
              </Button>
            </div>
            {!shots.data.length && <p>此项目尚无镜头。</p>}
          </>
        )}
      </section>
    </div>
  );
}

function Preview({ asset }: { asset: AssetDetail }) {
  const [failed, setFailed] = useState(false);
  return (
    <div className="asset-preview">
      {asset.mime_type.startsWith("video/") ? (
        <video
          controls
          preload="metadata"
          poster={assetApi.thumbnail(asset.id)}
          src={assetApi.file(asset.id)}
          onError={() => setFailed(true)}
        />
      ) : (
        <img
          alt={asset.name}
          src={assetApi.file(asset.id)}
          loading="lazy"
          onError={() => setFailed(true)}
        />
      )}
      {failed && (
        <p role="alert">
          当前浏览器无法预览此文件。
          <a href={assetApi.file(asset.id)} download={asset.original_filename}>
            打开原文件
          </a>
        </p>
      )}
    </div>
  );
}

export function AssetDetailSheet({
  id,
  onClose,
}: {
  id: string;
  onClose: () => void;
}) {
  const query = useAsset(id);
  const asset = query.data;
  const available = asset && !isMissingEntity(query.error);
  return (
    <DetailSheet
      open
      onOpenChange={(value) => {
        if (!value) onClose();
      }}
      title={available ? asset.name : "资产详情"}
      description="预览、标签与项目 / 镜头引用"
      preview={available ? <Preview asset={asset} /> : undefined}
    >
      {!available ? (
        <QueryState queries={[query]} />
      ) : (
        <>
          <QueryErrors queries={[query]} />
          <Content asset={asset} close={onClose} />
        </>
      )}
    </DetailSheet>
  );
}
