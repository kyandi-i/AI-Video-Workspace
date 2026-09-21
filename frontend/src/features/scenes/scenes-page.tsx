import { Layers } from "lucide-react";
import { EmptyState } from "@/components/common/empty-state";
import { QueryState } from "@/components/common/query-state";
import { useCurrentProject } from "@/features/projects/use-current-project";
import { useScripts } from "@/features/scripts/hooks";
import { ScriptEditor } from "@/features/scripts/script-editor";
import { useShots } from "@/features/shots/hooks";
import { useScenes } from "./hooks";
import { SceneEditor } from "./scene-editor";
import { SceneList } from "./scene-list";

export function Component() {
  const project = useCurrentProject();
  const scenes = useScenes(project.id);
  const scripts = useScripts(project.id);
  const shots = useShots(project.id);
  if (
    !scenes.data ||
    !scripts.data ||
    !shots.data ||
    scenes.isError ||
    scripts.isError ||
    shots.isError
  )
    return <QueryState queries={[scenes, scripts, shots]} />;
  const action = scripts.data.length ? (
    <SceneEditor projectId={project.id} scripts={scripts.data} />
  ) : (
    <ScriptEditor projectId={project.id} />
  );
  return (
    <div className="workflow-stack">
      <div className="section-toolbar">
        <div>
          <h2>Scenes</h2>
          <p>{scenes.data.length} 个场景 · 展开查看镜头</p>
        </div>
        {action}
      </div>
      {scenes.data.length ? (
        <SceneList
          projectId={project.id}
          scenes={scenes.data}
          scripts={scripts.data}
          shots={shots.data}
        />
      ) : (
        <EmptyState
          icon={Layers}
          title="还没有场景"
          description={
            scripts.data.length
              ? "创建第一个场景，开始组织这个剧本。"
              : "先创建剧本，再添加场景。"
          }
          action={action}
        />
      )}
    </div>
  );
}
