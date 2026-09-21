import { Button } from "@/components/ui/button";
import { EntityForm } from "@/components/common/entity-form";
import { useSceneMutations } from "./hooks";
import type { Scene } from "./types";
import type { Script } from "@/features/scripts/types";

export function SceneEditor({
  projectId,
  scripts,
  scriptId,
  scene,
}: {
  projectId: string;
  scripts: Script[];
  scriptId?: string;
  scene?: Scene;
}) {
  const { save } = useSceneMutations(projectId);
  return (
    <EntityForm
      title={scene ? "编辑场景" : "创建场景"}
      trigger={
        <Button size="sm" variant="secondary" disabled={!scripts.length}>
          {scene ? "编辑场景" : "创建场景"}
        </Button>
      }
      fields={[
        ...(!scene && !scriptId
          ? [
              {
                name: "script_id",
                label: "所属剧本",
                kind: "select" as const,
                required: true,
                options: scripts.map((script) => ({
                  value: script.id,
                  label: script.name,
                })),
              },
            ]
          : []),
        { name: "name", label: "场景名称", required: true, maxLength: 255 },
        { name: "description", label: "描述", kind: "textarea" },
        { name: "fixed_constraints", label: "固定约束", kind: "textarea" },
        { name: "negative_constraints", label: "负面约束", kind: "textarea" },
      ]}
      initial={{
        script_id: scene?.script_id ?? scriptId ?? scripts[0]?.id ?? "",
        name: scene?.name ?? "",
        description: scene?.description ?? "",
        fixed_constraints: scene?.fixed_constraints ?? "",
        negative_constraints: scene?.negative_constraints ?? "",
      }}
      onSave={(values) =>
        save.mutateAsync({
          id: scene?.id,
          scriptId: values.script_id,
          data: {
            name: values.name.trim(),
            description: values.description,
            fixed_constraints: values.fixed_constraints,
            negative_constraints: values.negative_constraints,
          },
        })
      }
    />
  );
}
