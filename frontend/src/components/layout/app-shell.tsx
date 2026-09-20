import {
  Clapperboard,
  LayoutDashboard,
  FolderOpen,
  Images,
  UsersRound,
  FileText,
  Settings2,
  HardDrive,
  ChevronRight,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

const upcoming = [
  { label: "项目", icon: FolderOpen, phase: 2 },
  { label: "资产库", icon: Images, phase: 3 },
  { label: "角色", icon: UsersRound, phase: 4 },
  { label: "Prompt 模板", icon: FileText, phase: 6 },
  { label: "设置", icon: Settings2, phase: 1 },
];

export function AppShell() {
  return (
    <div className="app-shell">
      <a href="#main" className="skip-link">
        跳到主要内容
      </a>
      <aside className="sidebar">
        <NavLink to="/" className="brand" aria-label="AI Video Workspace 首页">
          <span className="brand-icon">
            <Clapperboard size={23} />
          </span>
          <span>
            AI Video<span className="brand-subtitle">WORKSPACE</span>
          </span>
        </NavLink>
        <div className="workspace-switch">
          <span className="workspace-avatar">L</span>
          <div>
            本地工作空间<small>个人创作 · Local-first</small>
          </div>
          <ChevronRight size={14} />
        </div>
        <p className="nav-caption">工作台</p>
        <nav aria-label="主导航">
          <NavLink to="/" end className="nav-item active">
            <LayoutDashboard size={18} />
            <span>概览</span>
            <span className="active-dot" />
          </NavLink>
          {upcoming.map(({ label, icon: Icon, phase }) => (
            <button
              className="nav-item"
              key={label}
              disabled
              title={
                phase === 1
                  ? "Workspace API 已提供，设置页面后续开放"
                  : `将在 Phase ${phase} 开始实现`
              }
            >
              <Icon size={18} />
              <span>{label}</span>
              <small>待开发</small>
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="local-notice">
            <HardDrive size={18} />
            <div>
              创作，留在本地<small>你的素材与数据由你掌握</small>
            </div>
          </div>
          <div className="version-line">
            <span>MVP v0.1</span>
            <span>Phase 1</span>
          </div>
        </div>
      </aside>
      <div className="main-column">
        <header className="topbar">
          <div>
            工作空间 <ChevronRight size={14} />
            <strong>概览</strong>
          </div>
          <span className="local-badge">
            <span /> 本地运行
          </span>
        </header>
        <main id="main" tabIndex={-1}>
          <Outlet />
        </main>
        <footer className="page-footer">
          <span>AI VIDEO WORKSPACE</span>
          <span>从一个想法，到每一个镜头。</span>
        </footer>
      </div>
    </div>
  );
}
