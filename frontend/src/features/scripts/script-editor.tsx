import { Button } from "@/components/ui/button";
import { EntityForm } from "@/components/common/entity-form";
import { useScriptMutations } from "./hooks";
import type { Script } from "./types";

export function ScriptEditor({
  projectId,
  script,
}: {
  projectId: string;
  script?: Script;
}) {
  const { save } = useScriptMutations(projectId);
  return (
    <EntityForm
      title={script ? "编辑剧本" : "创建剧本"}
      trigger={
        <Button size="sm" variant={script ? "ghost" : "default"}>
          {script ? "编辑剧本" : "创建剧本"}
        </Button>
      }
      fields={[
        { name: "name", label: "剧本名称", required: true, maxLength: 255 },
        { name: "description", label: "描述", kind: "textarea" },
      ]}
      initial={{
        name: script?.name ?? "",
        description: script?.description ?? "",
      }}
      onSave={(values) =>
        save.mutateAsync({
          id: script?.id,
          data: { name: values.name.trim(), description: values.description },
        })
      }
    />
  );
}
