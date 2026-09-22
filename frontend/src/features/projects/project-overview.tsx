import { isMissingEntity } from "@/api/client";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { WorkspacePanel } from "@/components/common/workspace-panel";
import { QueryState, QueryErrors } from "@/components/common/query-state";
import { useCurrentProject } from "./use-current-project";
import { useProjectStats } from "./hooks";

export function Component() {
  const project = useCurrentProject();
  const stats = useProjectStats(project.id);
  if (!stats.data || isMissingEntity(stats.error))
    return <QueryState queries={[stats]} />;
  return (
    <>
      <QueryErrors queries={[stats]} />
      <section className="status-strip" aria-label="项目统计">
        {(
          [
            ["scripts", "Scripts"],
            ["scenes", "Scenes"],
            ["shots", "Shots"],
          ] as const
        ).map(([key, label]) => (
          <div key={key}>
            <span className="status-label">{label}</span>
            <strong>{stats.data[key]}</strong>
          </div>
        ))}
      </section>
      <WorkspacePanel
        title="制作结构"
        description="从剧本开始，为每个场景建立镜头。"
      >
        <div className="overview-links">
          {[
            ["script", "Script", "组织剧本与场景层级"],
            ["scenes", "Scenes", "查看场景与空间约束"],
            ["shots", "Shots", "搜索镜头与跟进状态"],
            ["characters", "Characters", "管理角色与视觉状态"],
          ].map(([path, label, description]) => (
            <div key={path}>
              <strong>{label}</strong>
              <p>{description}</p>
              <Button variant="secondary" asChild size="sm">
                <Link to={`/projects/${project.id}/${path}`}>打开 {label}</Link>
              </Button>
            </div>
          ))}
        </div>
      </WorkspacePanel>
    </>
  );
}
