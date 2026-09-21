import { Link, useParams } from "react-router-dom";
import { ScanLine } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/common/page-header";
import { WorkspacePanel } from "@/components/common/workspace-panel";
import { QueryState } from "@/components/common/query-state";
import { EmptyState } from "@/components/common/empty-state";
import { useScenes } from "@/features/scenes/hooks";
import { ShotEditor } from "./shot-editor";
import { useShot } from "./hooks";
import type { Shot } from "./types";

function Detail({ shot }: { shot: Shot }) {
  const scenes = useScenes(shot.project_id);
  if (!scenes.data || scenes.isError) return <QueryState queries={[scenes]} />;
  return (
    <div className="workspace-page">
      <Link className="back-link" to={`/projects/${shot.project_id}/shots`}>
        ← 返回镜头列表
      </Link>
      <PageHeader
        title={`${shot.shot_code} · ${shot.title}`}
        metadata={<Badge>{shot.status}</Badge>}
        actions={
          <ShotEditor
            projectId={shot.project_id}
            scenes={scenes.data}
            shot={shot}
          />
        }
      />
      <WorkspacePanel title="镜头信息">
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
  return shot.isPending || shot.isError ? (
    <QueryState queries={[shot]} />
  ) : (
    <Detail shot={shot.data} />
  );
}
