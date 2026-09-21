import { isMissingEntity } from "@/api/client";
import { shotStatusOptions } from "@/lib/status-display";
import { Link, useSearchParams } from "react-router-dom";
import { ScanLine } from "lucide-react";
import { SearchInput } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { QueryState, QueryErrors } from "@/components/common/query-state";
import { EmptyState } from "@/components/common/empty-state";
import { Choice } from "@/components/common/entity-form";
import { useCurrentProject } from "@/features/projects/use-current-project";
import { useScenes } from "@/features/scenes/hooks";
import { useShots } from "./hooks";
import { ShotEditor } from "./shot-editor";
import { ShotTable } from "./shot-table";

export function Component() {
  const project = useCurrentProject();
  const shots = useShots(project.id);
  const scenes = useScenes(project.id);
  const [params, setParams] = useSearchParams();
  const search = params.get("q") ?? "";
  const scene = params.get("scene") ?? "all";
  const status = params.get("status") ?? "all";
  const setFilter = (key: string, value: string) =>
    setParams(
      (current) => {
        const next = new URLSearchParams(current);
        if (!value || value === "all") next.delete(key);
        else next.set(key, value);
        return next;
      },
      { replace: true },
    );
  const hasFilters = Boolean(search || scene !== "all" || status !== "all");
  if (
    !shots.data ||
    !scenes.data ||
    isMissingEntity(shots.error) ||
    isMissingEntity(scenes.error)
  )
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
      <QueryErrors queries={[shots, scenes]} />
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
        <SearchInput
          aria-label="搜索镜头"
          placeholder="搜索编号或标题…"
          value={search}
          onChange={(event) => setFilter("q", event.target.value)}
        />
        <Choice
          label="场景筛选"
          value={scene}
          onChange={(value) => setFilter("scene", value)}
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
          onChange={(value) => setFilter("status", value)}
          options={[{ value: "all", label: "全部状态" }, ...shotStatusOptions]}
        />
      </div>
      {hasFilters && filtered.length > 0 && (
        <div>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => setParams({}, { replace: true })}
          >
            清除筛选
          </Button>
        </div>
      )}
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
      ) : shots.data.length > 0 && !filtered.length ? (
        <EmptyState
          compact
          icon={ScanLine}
          title="没有匹配的镜头"
          description="尝试其他编号或标题，或清除场景与状态筛选。"
          action={
            <Button
              variant="secondary"
              onClick={() => setParams({}, { replace: true })}
            >
              清除筛选
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
