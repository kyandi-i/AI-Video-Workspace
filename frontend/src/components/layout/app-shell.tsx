import {
  Clapperboard,
  LayoutDashboard,
  FolderOpen,
  Images,
  FileText,
  Settings2,
  HardDrive,
  ChevronRight,
  Moon,
  Sun,
  CircleHelp,
  Trash2,
} from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useTheme } from "@/lib/theme";
import { useHealth } from "@/features/dashboard/use-health";

const navigation = [{ label: "Prompt Templates", icon: FileText }];

export function AppShell() {
  const { theme, setTheme } = useTheme();
  const health = useHealth();
  const location = useLocation();
  const page =
    location.pathname === "/"
      ? "Overview"
      : location.pathname === "/settings"
        ? "Settings"
        : location.pathname === "/assets"
          ? "Asset Library"
          : location.pathname.startsWith("/projects")
            ? "Projects"
            : location.pathname.startsWith("/shots/")
              ? location.pathname.endsWith("/workspace")
                ? "Shot Workspace"
                : "Shot Detail"
              : "Workspace";
  return (
    <div className="app-shell">
      <a href="#main" className="skip-link">
        跳到主要内容
      </a>
      <aside className="sidebar">
        <NavLink to="/" className="brand" aria-label="AI Video Workspace 首页">
          <span className="brand-mark">
            <Clapperboard size={21} />
          </span>
          <div>
            <strong>AI Video</strong>
            <span>WORKSPACE</span>
          </div>
        </NavLink>
        <div className="workspace-identity">
          <span className="workspace-symbol">
            <HardDrive size={16} />
          </span>
          <div>
            <strong>Local workspace</strong>
            <span>个人工作空间</span>
          </div>
        </div>
        <span className="nav-label">WORKSPACE</span>
        <nav aria-label="主导航">
          <NavLink to="/recycle-bin" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
            <Trash2 size={17} /><span>Recycle Bin</span>
          </NavLink>
          <NavLink
            to="/"
            end
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
          >
            <LayoutDashboard size={17} />
            <span>Dashboard</span>
          </NavLink>
          <NavLink
            to="/projects"
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
          >
            <FolderOpen size={17} />
            <span>Projects</span>
          </NavLink>
          <NavLink
            to="/assets"
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
          >
            <Images size={17} />
            <span>Asset Library</span>
          </NavLink>
          {navigation.map(({ label, icon: Icon }) => (
            <NavLink
              key={label}
              to="/prompt-templates"
              className={({ isActive }) =>
                `nav-item ${isActive ? "active" : ""}`
              }
              aria-label={label}
            >
              <Icon size={17} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <NavLink
            to="/settings"
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
          >
            <Settings2 size={17} />
            <span>Settings</span>
          </NavLink>
          <div className="sidebar-footnote">
            <HardDrive size={13} />
            <span>Local-first · 你的数据留在本机</span>
          </div>
        </div>
      </aside>
      <div className="main-column">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span>
            <ChevronRight size={13} />
            <strong>{page}</strong>
          </div>
          <div className="topbar-actions">
            <span
              className={`connection-indicator ${health.isSuccess && !health.isError ? "is-online" : "is-offline"}`}
              role="status"
            >
              <i />
              {health.isPending
                ? "连接中"
                : health.isError
                  ? "连接中断"
                  : "Local · 已连接"}
            </span>
            <span className="topbar-divider" />
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={
                    theme === "dark" ? "切换到浅色模式" : "切换到深色模式"
                  }
                  onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                >
                  {theme === "dark" ? <Sun /> : <Moon />}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                {theme === "dark" ? "Light mode" : "Dark mode"}
              </TooltipContent>
            </Tooltip>
            <Button variant="ghost" size="icon" asChild>
              <a href="/settings" aria-label="工作空间设置">
                <CircleHelp />
              </a>
            </Button>
          </div>
        </header>
        <main id="main" tabIndex={-1}>
          <Outlet />
        </main>
        <footer className="workspace-footer">
          <span>AI VIDEO WORKSPACE</span>
          <span>
            LOCAL STORAGE <span className="footer-dot">·</span> PRIVATE BY
            DEFAULT
          </span>
        </footer>
      </div>
    </div>
  );
}
