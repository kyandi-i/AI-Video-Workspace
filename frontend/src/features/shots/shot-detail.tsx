import { ShotCharacters } from "@/features/characters/shot-characters";
import { isMissingEntity } from "@/api/client";
import { StatusBadge } from "@/components/common/status-badge";
import { Link, useLocation, useParams } from "react-router-dom";
import { ScanLine } from "lucide-react";
import { PageHeader } from "@/components/common/page-header";
import { WorkspacePanel } from "@/components/common/workspace-panel";
import { QueryState, QueryErrors } from "@/components/common/query-state";
import { EmptyState } from "@/components/common/empty-state";
import { useScenes } from "@/features/scenes/hooks";
import { ShotEditor } from "./shot-editor";
import { useShot } from "./hooks";
import type { Shot } from "./types";

function Detail({ shot }: { shot: Shot }) {
  const location = useLocation();
  const previous = (location.state as { returnTo?: string } | null)?.returnTo;
  const returnTo =
    previous &&
    ["script", "scenes", "shots"].some(
      (page) =>
        previous.split("?")[0] === `/projects/${shot.project_id}/${page}`,
    )
      ? previous
      : `/projects/${shot.project_id}/shots`;
  const returnLabel = returnTo.split("?")[0].endsWith("/script")
    ? "返回剧本"
    : returnTo.split("?")[0].endsWith("/scenes")
      ? "返回场景列表"
      : "返回镜头列表";
  const scenes = useScenes(shot.project_id);
  if (!scenes.data || isMissingEntity(scenes.error))
    return <QueryState queries={[scenes]} />;
  return (
    <div className="workspace-page">
      <QueryErrors queries={[scenes]} />
      <Link className="back-link" to={returnTo}>
        ← {returnLabel}
      </Link>
      <PageHeader
        title={`${shot.shot_code} · ${shot.title}`}
        metadata={<StatusBadge status={shot.status} />}
        actions={
          <ShotEditor
            projectId={shot.project_id}
            scenes={scenes.data}
            shot={shot}
          />
        }
      />
      <WorkspacePanel title="镜头信息">
        <Link className="back-link" to={`/assets?shot_id=${shot.id}`}>
          查看关联资产 →
        </Link>
        <dl className="shot-facts">
          <div>
            <dt>场景</dt>
            <dd>
              <Link to={`/projects/${shot.project_id}/scenes`}>
                {scenes.data.find((scene) => scene.id === shot.scene_id)?.name}
              </Link>
            </dd>
          </div>
          <div>
            <dt>时长</dt>
            <dd>{shot.duration_seconds} 秒</dd>
          </div>
          <div>
            <dt>描述</dt>
            <dd>{shot.description || "未填写描述"}</dd>
          </div>
          <div>
            <dt>创作要求</dt>
            <dd>{shot.creative_requirement || "未填写创作要求"}</dd>
          </div>
        </dl>
      </WorkspacePanel>
      <ShotCharacters shotId={shot.id} projectId={shot.project_id} />
      <EmptyState
        compact
        icon={ScanLine}
        title="更多制作工具尚未加入"
        description="你可以先完善镜头内容与创作要求。"
      />
    </div>
  );
}
export function Component() {
  const { shotId = "" } = useParams();
  const shot = useShot(shotId);
  return !shot.data || isMissingEntity(shot.error) ? (
    <QueryState queries={[shot]} />
  ) : (
    <>
      <QueryErrors queries={[shot]} />
      <Detail shot={shot.data} />
    </>
  );
}
