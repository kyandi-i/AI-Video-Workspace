import { StatusBadge } from "@/components/common/status-badge";
import { ArrowDown, ArrowUp, ScanLine } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { EmptyState } from "@/components/common/empty-state";
import { Button } from "@/components/ui/button";
import { DeleteEntity } from "@/components/common/entity-form";
import { notify } from "@/lib/notifications";
import { ShotEditor } from "./shot-editor";
import { useShotMutations } from "./hooks";
import type { Shot } from "./types";
import type { Scene } from "@/features/scenes/types";

export function ShotTable({
  projectId,
  shots,
  allShots = shots,
  scenes,
  sceneId,
}: {
  projectId: string;
  shots: Shot[];
  allShots?: Shot[];
  scenes: Scene[];
  sceneId?: string;
}) {
  const location = useLocation();
  const returnTo = location.pathname + location.search;
  const { remove, move } = useShotMutations(projectId);
  if (!shots.length)
    return (
      <EmptyState
        compact
        icon={ScanLine}
        title="还没有镜头"
        description="创建第一个镜头，填写画面内容与创作要求。"
        action={
          <ShotEditor projectId={projectId} scenes={scenes} sceneId={sceneId} />
        }
      />
    );
  return (
    <div className="table-scroll">
      <table className="shot-table">
        <thead>
          <tr>
            <th>编号 / 标题</th>
            <th>场景</th>
            <th>时长</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {shots.map((shot) => (
            <tr key={shot.id} aria-label={`${shot.shot_code} ${shot.title}`}>
              <td>
                <Link
                  className="shot-link"
                  to={`/shots/${shot.id}`}
                  state={{ returnTo }}
                >
                  <span title={shot.shot_code}>{shot.shot_code}</span>
                  <strong title={shot.title}>{shot.title}</strong>
                </Link>
              </td>
              <td>
                <span
                  className="table-scene-name"
                  title={
                    scenes.find((scene) => scene.id === shot.scene_id)?.name
                  }
                >
                  {scenes.find((scene) => scene.id === shot.scene_id)?.name ??
                    "—"}
                </span>
              </td>
              <td>{shot.duration_seconds}s</td>
              <td>
                <StatusBadge status={shot.status} />
              </td>
              <td>
                <div className="row-actions">
                  <Button size="sm" variant="ghost" asChild>
                    <Link to={`/shots/${shot.id}`} state={{ returnTo }}>
                      打开
                    </Link>
                  </Button>
                  <Button size="sm" variant="ghost" asChild>
                    <Link
                      to={`/shots/${shot.id}/workspace`}
                      state={{ returnTo }}
                    >
                      Workspace
                    </Link>
                  </Button>
                  <ShotEditor
                    projectId={projectId}
                    scenes={scenes}
                    shot={shot}
                  />
                  {(["up", "down"] as const).map((direction) => (
                    <Button
                      key={direction}
                      variant="ghost"
                      size="icon"
                      aria-label={`${direction === "up" ? "上移" : "下移"} ${shot.shot_code}`}
                      disabled={
                        move.isPending ||
                        (direction === "up"
                          ? shot.order_index === 0
                          : shot.order_index >=
                            allShots.filter(
                              (item) => item.scene_id === shot.scene_id,
                            ).length -
                              1)
                      }
                      onClick={() =>
                        move.mutate(
                          { id: shot.id, direction },
                          {
                            onError: (error) => notify.error(error.message),
                            onSuccess: () => notify.success("顺序已更新"),
                          },
                        )
                      }
                    >
                      {direction === "up" ? <ArrowUp /> : <ArrowDown />}
                    </Button>
                  ))}
                  <DeleteEntity
                    name={shot.shot_code}
                    description={`镜头「${shot.title}」将从场景中移除。`}
                    onDelete={() =>
                      remove.mutateAsync({
                        id: shot.id,
                        sceneId: shot.scene_id,
                      })
                    }
                  />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
