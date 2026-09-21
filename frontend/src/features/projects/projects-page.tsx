import { FolderOpen } from "lucide-react";
import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/common/page-header";
import { EntityCard } from "@/components/common/entity-card";
import { EmptyState } from "@/components/common/empty-state";
import { QueryState } from "@/components/common/query-state";
import { DeleteEntity } from "@/components/common/entity-form";
import { ProjectEditor } from "./project-editor";
import { useProjects, useProjectMutations } from "./hooks";

export function Component() {
  const projects = useProjects();
  const { remove } = useProjectMutations();
  return (
    <div className="workspace-page">
      <PageHeader
        title="Projects"
        description="组织项目、剧本、场景与镜头。"
        actions={<ProjectEditor />}
      />
      {projects.isPending || projects.isError ? (
        <QueryState queries={[projects]} />
      ) : !projects.data.length ? (
        <EmptyState
          icon={FolderOpen}
          title="还没有项目"
          description="创建第一个项目，开始组织视频内容。"
          action={<ProjectEditor />}
        />
      ) : (
        <div className="project-grid">
          {projects.data.map((project) => (
            <article
              key={project.id}
              className="project-item"
              aria-label={project.name}
            >
              <EntityCard
                name={project.name}
                status={<Badge>{project.status}</Badge>}
                metadata={
                  <>
                    <p className="text-summary">
                      {project.description || "未填写描述"}
                    </p>
                    <span>
                      更新于 {new Date(project.updated_at).toLocaleString()}
                    </span>
                  </>
                }
              />
              <div className="entity-actions">
                <Button asChild size="sm">
                  <Link to={`/projects/${project.id}`}>打开项目</Link>
                </Button>
                <ProjectEditor project={project} />
                <DeleteEntity
                  name={project.name}
                  description="项目下的剧本、场景和镜头也会一并删除。"
                  onDelete={() => remove.mutateAsync(project.id)}
                />
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
