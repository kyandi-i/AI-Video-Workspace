import { useState } from "react";
import { Link } from "react-router-dom";
import { ScanLine } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { QueryState } from "@/components/common/query-state";
import { EmptyState } from "@/components/common/empty-state";
import { Choice } from "@/components/common/entity-form";
import { useCurrentProject } from "@/features/projects/use-current-project";
import { useScenes } from "@/features/scenes/hooks";
import { useShots } from "./hooks";
import { ShotEditor } from "./shot-editor";
import { ShotTable } from "./shot-table";
import { shotStatuses } from "./types";

export function Component() {
  const project = useCurrentProject();
  const shots = useShots(project.id);
  const scenes = useScenes(project.id);
  const [search, setSearch] = useState("");
  const [scene, setScene] = useState("all");
  const [status, setStatus] = useState("all");
  if (!shots.data || !scenes.data || shots.isError || scenes.isError)
    return <QueryState queries={[shots, scenes]} />;
  const filtered = shots.data.filter(
    (shot) =>
      (scene === "all" || scene === shot.scene_id) &&
      (status === "all" || status === shot.status) &&
      `${shot.shot_code} ${shot.title}`
        .toLocaleLowerCase()
        .includes(search.trim().toLocaleLowerCase()),
  );
  return (
    <div className="workflow-stack">
      <div className="section-toolbar">
        <div>
          <h2>Shots</h2>
          <p>
            {filtered.length} / {shots.data.length} 个镜头
          </p>
        </div>
        <ShotEditor projectId={project.id} scenes={scenes.data} />
      </div>
      <div className="shot-filters">
        <Input
          aria-label="搜索镜头"
          placeholder="搜索编号或标题…"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <Choice
          label="场景筛选"
          value={scene}
          onChange={setScene}
          options={[
            { value: "all", label: "全部场景" },
            ...scenes.data.map((item) => ({
              value: item.id,
              label: item.name,
            })),
          ]}
        />
        <Choice
          label="状态筛选"
          value={status}
          onChange={setStatus}
          options={[
            { value: "all", label: "全部状态" },
            ...shotStatuses.map((value) => ({ value, label: value })),
          ]}
        />
      </div>
      {!scenes.data.length ? (
        <EmptyState
          icon={ScanLine}
          title="先建立场景"
          description="打开剧本，为项目创建场景后即可添加镜头。"
          action={
            <Button asChild>
              <Link to={`/projects/${project.id}/script`}>打开 Script</Link>
            </Button>
          }
        />
      ) : (
        <ShotTable
          projectId={project.id}
          shots={filtered}
          allShots={shots.data}
          scenes={scenes.data}
        />
      )}
    </div>
  );
}
