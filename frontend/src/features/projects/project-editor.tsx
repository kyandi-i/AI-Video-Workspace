import { projectStatusOptions } from "@/lib/status-display";
import { Button } from "@/components/ui/button";
import { EntityForm } from "@/components/common/entity-form";
import { useProjectMutations } from "./hooks";
import { type Project, type ProjectStatus } from "./types";

export function ProjectEditor({ project }: { project?: Project }) {
  const { save } = useProjectMutations();
  return (
    <EntityForm
      title={project ? "编辑项目" : "创建项目"}
      trigger={
        <Button size="sm" variant={project ? "secondary" : "default"}>
          {project ? "编辑项目" : "创建项目"}
        </Button>
      }
      fields={[
        { name: "name", label: "项目名称", required: true, maxLength: 255 },
        { name: "description", label: "描述", kind: "textarea" },
        {
          name: "status",
          label: "状态",
          kind: "select",
          options: projectStatusOptions,
        },
      ]}
      initial={{
        name: project?.name ?? "",
        description: project?.description ?? "",
        status: project?.status ?? "DRAFT",
      }}
      onSave={(values) =>
        save.mutateAsync({
          id: project?.id,
          data: {
            name: values.name.trim(),
            description: values.description,
            status: values.status as ProjectStatus,
          },
        })
      }
    />
  );
}
