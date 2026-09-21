import { FileText, Layers } from "lucide-react";
import { WorkspacePanel } from "@/components/common/workspace-panel";
import { EmptyState } from "@/components/common/empty-state";
import { QueryState } from "@/components/common/query-state";
import { DeleteEntity } from "@/components/common/entity-form";
import { useCurrentProject } from "@/features/projects/use-current-project";
import { useScenes } from "@/features/scenes/hooks";
import { SceneList } from "@/features/scenes/scene-list";
import { SceneEditor } from "@/features/scenes/scene-editor";
import { useShots } from "@/features/shots/hooks";
import { useScripts, useScriptMutations } from "./hooks";
import { ScriptEditor } from "./script-editor";

export function Component() {
  const project = useCurrentProject();
  const scripts = useScripts(project.id);
  const scenes = useScenes(project.id);
  const shots = useShots(project.id);
  const { remove } = useScriptMutations(project.id);
  if (
    !scripts.data ||
    !scenes.data ||
    !shots.data ||
    scripts.isError ||
    scenes.isError ||
    shots.isError
  )
    return <QueryState queries={[scripts, scenes, shots]} />;
  return (
    <div className="workflow-stack">
      <div className="section-toolbar">
        <div>
          <h2>Script</h2>
          <p>按场景组织镜头，建立完整的制作结构。</p>
        </div>
        <ScriptEditor projectId={project.id} />
      </div>
      {!scripts.data.length ? (
        <EmptyState
          icon={FileText}
          title="还没有剧本"
          description="创建剧本，再添加场景和镜头。"
          action={<ScriptEditor projectId={project.id} />}
        />
      ) : (
        scripts.data.map((script) => {
          const children = scenes.data.filter(
            (scene) => scene.script_id === script.id,
          );
          return (
            <WorkspacePanel
              key={script.id}
              title={script.name}
              description={script.description}
              metadata={`${children.length} scenes`}
              actions={
                <>
                  <SceneEditor
                    projectId={project.id}
                    scripts={scripts.data}
                    scriptId={script.id}
                  />
                  <ScriptEditor projectId={project.id} script={script} />
                  <DeleteEntity
                    name={script.name}
                    description="剧本及其场景、镜头会一并删除。"
                    onDelete={() => remove.mutateAsync(script.id)}
                  />
                </>
              }
            >
              {children.length ? (
                <SceneList
                  projectId={project.id}
                  scenes={children}
                  scripts={scripts.data}
                  shots={shots.data}
                />
              ) : (
                <EmptyState
                  compact
                  icon={Layers}
                  title="还没有场景"
                  description="创建第一个场景，开始组织这个剧本。"
                  action={
                    <SceneEditor
                      projectId={project.id}
                      scripts={scripts.data}
                      scriptId={script.id}
                    />
                  }
                />
              )}
            </WorkspacePanel>
          );
        })
      )}
    </div>
  );
}
