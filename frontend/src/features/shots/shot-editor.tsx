import { Button } from "@/components/ui/button";
import { EntityForm } from "@/components/common/entity-form";
import { useShotMutations } from "./hooks";
import { shotStatuses, type Shot, type ShotStatus } from "./types";
import type { Scene } from "@/features/scenes/types";

export function ShotEditor({
  projectId,
  scenes,
  sceneId,
  shot,
}: {
  projectId: string;
  scenes: Scene[];
  sceneId?: string;
  shot?: Shot;
}) {
  const { save } = useShotMutations(projectId);
  return (
    <EntityForm
      title={shot ? "编辑镜头" : "创建镜头"}
      trigger={
        <Button
          size="sm"
          variant={shot ? "ghost" : "secondary"}
          disabled={!scenes.length}
        >
          {shot ? "编辑镜头" : "创建镜头"}
        </Button>
      }
      fields={[
        ...(!shot && !sceneId
          ? [
              {
                name: "scene_id",
                label: "所属场景",
                kind: "select" as const,
                required: true,
                options: scenes.map((scene) => ({
                  value: scene.id,
                  label: scene.name,
                })),
              },
            ]
          : []),
        { name: "shot_code", label: "镜头编号", required: true, maxLength: 80 },
        { name: "title", label: "镜头标题", required: true, maxLength: 255 },
        { name: "description", label: "描述", kind: "textarea" },
        {
          name: "duration_seconds",
          label: "时长（秒）",
          kind: "number",
          required: true,
        },
        {
          name: "status",
          label: "状态",
          kind: "select",
          options: shotStatuses.map((value) => ({ value, label: value })),
        },
        { name: "creative_requirement", label: "创作要求", kind: "textarea" },
      ]}
      initial={{
        scene_id: shot?.scene_id ?? sceneId ?? scenes[0]?.id ?? "",
        shot_code: shot?.shot_code ?? "",
        title: shot?.title ?? "",
        description: shot?.description ?? "",
        duration_seconds: String(shot?.duration_seconds ?? 0),
        status: shot?.status ?? "DRAFT",
        creative_requirement: shot?.creative_requirement ?? "",
      }}
      onSave={(values) =>
        save.mutateAsync({
          id: shot?.id,
          sceneId: values.scene_id,
          data: {
            shot_code: values.shot_code.trim(),
            title: values.title.trim(),
            description: values.description,
            duration_seconds: Number(values.duration_seconds),
            status: values.status as ShotStatus,
            creative_requirement: values.creative_requirement,
          },
        })
      }
    />
  );
}
