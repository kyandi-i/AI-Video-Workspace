import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DeleteEntity } from "@/components/common/entity-form";
import { ShotEditor } from "@/features/shots/shot-editor";
import { ShotTable } from "@/features/shots/shot-table";
import type { Shot } from "@/features/shots/types";
import type { Script } from "@/features/scripts/types";
import { SceneEditor } from "./scene-editor";
import { useSceneMutations } from "./hooks";
import type { Scene } from "./types";

export function SceneList({
  projectId,
  scenes,
  scripts,
  shots,
}: {
  projectId: string;
  scenes: Scene[];
  scripts: Script[];
  shots: Shot[];
}) {
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const { remove } = useSceneMutations(projectId);
  return (
    <div className="scene-list">
      {scenes.map((scene) => (
        <section
          className="scene-section"
          key={scene.id}
          aria-label={`场景 ${scene.name}`}
        >
          <div className="scene-heading">
            <Button
              size="icon"
              variant="ghost"
              aria-label={`${collapsed[scene.id] ? "展开" : "收起"} ${scene.name}`}
              aria-expanded={!collapsed[scene.id]}
              onClick={() =>
                setCollapsed((current) => ({
                  ...current,
                  [scene.id]: !current[scene.id],
                }))
              }
            >
              {collapsed[scene.id] ? <ChevronRight /> : <ChevronDown />}
            </Button>
            <span className="scene-order">
              {String(scene.order_index + 1).padStart(2, "0")}
            </span>
            <div className="scene-title">
              <h3 title={scene.name}>{scene.name}</h3>
              <span>
                {scene.shot_count} shots ·{" "}
                {scripts.find((script) => script.id === scene.script_id)?.name}
              </span>
            </div>
            <div className="row-actions">
              <ShotEditor
                projectId={projectId}
                scenes={scenes}
                sceneId={scene.id}
              />
              <SceneEditor
                projectId={projectId}
                scripts={scripts}
                scene={scene}
              />
              <DeleteEntity
                name={scene.name}
                description={`场景及其 ${scene.shot_count} 个镜头会一并删除。`}
                onDelete={() => remove.mutateAsync(scene.id)}
              />
            </div>
          </div>
          {scene.description && (
            <p className="scene-description">{scene.description}</p>
          )}
          {!collapsed[scene.id] && (
            <ShotTable
              projectId={projectId}
              shots={shots.filter((shot) => shot.scene_id === scene.id)}
              scenes={scenes}
              sceneId={scene.id}
            />
          )}
        </section>
      ))}
    </div>
  );
}
