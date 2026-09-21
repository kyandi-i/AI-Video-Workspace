import { NavLink, Outlet, useParams, Link } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/common/page-header";
import { QueryState } from "@/components/common/query-state";
import { ProjectEditor } from "./project-editor";
import { useProject } from "./hooks";

export function Component() {
  const { projectId = "" } = useParams();
  const project = useProject(projectId);
  if (project.isPending || project.isError)
    return <QueryState queries={[project]} />;
  return (
    <div className="workspace-page">
      <Link className="back-link" to="/projects">
        ← Projects
      </Link>
      <PageHeader
        title={project.data.name}
        description={project.data.description || "项目工作空间"}
        metadata={<Badge>{project.data.status}</Badge>}
        actions={<ProjectEditor project={project.data} />}
      />
      <nav className="project-tabs" aria-label="项目导航">
        {[
          ["", "Overview"],
          ["script", "Script"],
          ["scenes", "Scenes"],
          ["shots", "Shots"],
        ].map(([path, label]) => (
          <NavLink
            key={label}
            end
            to={`/projects/${projectId}${path ? `/${path}` : ""}`}
            className={({ isActive }) => (isActive ? "active" : "")}
          >
            {label}
          </NavLink>
        ))}
      </nav>
      <Outlet context={project.data} />
    </div>
  );
}
