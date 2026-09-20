import {
  ArrowDown,
  ArrowRight,
  Check,
  Circle,
  Clapperboard,
  Database,
  ExternalLink,
  Film,
  FolderOpen,
  HardDrive,
  Layers3,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useHealth } from "./use-health";

const steps = [
  {
    icon: FolderOpen,
    title: "组织项目",
    text: "剧本 / 场景 / 镜头",
    phase: "PHASE 02",
  },
  {
    icon: Layers3,
    title: "准备素材",
    text: "资产 / 角色 / 状态",
    phase: "PHASE 03–05",
  },
  {
    icon: Sparkles,
    title: "构思分镜",
    text: "模板 / Prompt / 版本",
    phase: "PHASE 06–08",
  },
  {
    icon: Film,
    title: "完成镜头",
    text: "分镜导入 / 视频结果",
    phase: "PHASE 09–10",
  },
];

export function DashboardPage() {
  const health = useHealth();
  const connected = health.isSuccess && !health.isError;
  return (
    <div className="dashboard">
      <section className="page-heading">
        <div>
          <p className="eyebrow">YOUR CREATIVE SPACE</p>
          <h1>创作工作台</h1>
          <p className="muted">让想法、素材与镜头，在同一个地方有序生长。</p>
        </div>
        <span className="phase-pill">
          <span /> Phase 1 · 数据与文件基础
        </span>
      </section>

      <section className="welcome-card">
        <div className="welcome-copy">
          <span className="mini-label">
            <Sparkles size={14} /> 为 AI 视频创作而生
          </span>
          <h2>
            每个好故事，
            <br />
            从一个清晰的工作空间开始。
          </h2>
          <p>
            串联你的制作流程，专注每一帧的表达。
            <br />
            本地工作台已搭建，接下来逐步开启创作工具。
          </p>
          <Button asChild>
            <a href="#roadmap">
              查看开发路线 <ArrowRight />
            </a>
          </Button>
        </div>
        <div className="story-illustration" aria-hidden="true">
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <div className="story-card back-card">
            <div className="frame-label">THE NEXT SCENE</div>
            <div className="abstract-scene">
              <div className="sun" />
              <div className="hill hill-one" />
              <div className="hill hill-two" />
            </div>
            <div className="frame-bottom">
              <span>01 / STORYBOARD</span>
              <span>···</span>
            </div>
          </div>
          <div className="story-card front-card">
            <div className="frame-label">
              <Clapperboard size={12} /> YOUR STORY STARTS HERE
            </div>
            <div className="story-grid">
              {Array.from({ length: 6 }, (_, i) => (
                <span key={i}>
                  <i />
                  {String(i + 1).padStart(2, "0")}
                </span>
              ))}
            </div>
            <div className="frame-bottom">
              <span>想法 → 镜头 → 故事</span>
              <span className="green-dot" />
            </div>
          </div>
          <span className="floating-label">
            <span className="green-dot" /> Made for your workflow
          </span>
        </div>
      </section>

      <section className="status-grid" aria-label="运行状态">
        <article className="status-card">
          <span className={`status-icon ${connected ? "green" : "amber"}`}>
            <HardDrive size={20} />
          </span>
          <div>
            <span className="muted small">本地服务</span>
            <h3 role="status">
              {health.isPending
                ? "正在连接…"
                : connected
                  ? "连接正常"
                  : "连接中断"}
            </h3>
            <p>
              {connected
                ? `FastAPI · v${health.data.version}`
                : health.isPending
                  ? "检查后端运行状态"
                  : "请检查后端服务是否启动"}
            </p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => void health.refetch()}
            disabled={health.isFetching}
            aria-label="重新检查连接"
          >
            <RefreshCw className={health.isFetching ? "animate-spin" : ""} />
          </Button>
        </article>
        <article className="status-card">
          <span className="status-icon violet">
            <Database size={20} />
          </span>
          <div>
            <span className="muted small">数据与存储</span>
            <h3>
              {connected && health.data.storage_initialized
                ? "存储已初始化"
                : "等待服务确认"}
            </h3>
            <p>SQLite + 托管文件 · Phase 1</p>
          </div>
          <span className="tiny-tag">基础设施</span>
        </article>
        <article className="status-card">
          <span className="status-icon blue">
            <Clapperboard size={20} />
          </span>
          <div>
            <span className="muted small">制作空间</span>
            <h3>准备就绪</h3>
            <p>前端框架与页面布局已建立</p>
          </div>
          <Check className="text-muted-foreground" size={18} />
        </article>
      </section>
      {health.isError && (
        <div role="alert" className="error-banner">
          暂时无法连接本地服务。{health.error.message}
          。服务恢复后会自动重连，也可以点击上方刷新按钮。
        </div>
      )}

      <section className="workflow-section">
        <div className="section-heading">
          <div>
            <h2>从想法到成片</h2>
            <p>围绕镜头组织制作，让每一步都有迹可循。</p>
          </div>
          <span className="subtle-label">逐阶段开放</span>
        </div>
        <div className="workflow-grid">
          {steps.map(({ icon: Icon, title, text, phase }, i) => (
            <article key={title} className="workflow-card">
              <div className="workflow-top">
                <span className="workflow-icon">
                  <Icon size={21} />
                </span>
                <span className="step-number">0{i + 1}</span>
              </div>
              <h3>{title}</h3>
              <p>{text}</p>
              <div className="workflow-bottom">
                <span>{phase}</span>
                {i < steps.length - 1 && <ArrowRight size={16} />}
              </div>
            </article>
          ))}
        </div>
      </section>

      <div className="bottom-grid">
        <section id="roadmap" className="roadmap panel">
          <div className="section-heading">
            <div>
              <h2>一步一步，开始创作</h2>
              <p>当前阶段：数据与文件基础</p>
            </div>
            <span className="tiny-tag">开发进度</span>
          </div>
          <ol>
            <li>
              <span className="timeline-dot">
                <Check size={13} />
              </span>
              <div>
                <h3>Phase 0 · 项目初始化</h3>
                <p>前后端启动、连接检查与本地运行入口</p>
              </div>
              <span className="current-label">已完成</span>
            </li>
            <li className="current">
              <span className="timeline-dot">
                <Check size={13} />
              </span>
              <div>
                <h3>Phase 1 · 数据与文件基础</h3>
                <p>数据库迁移、Workspace 与 Storage 抽象</p>
              </div>
              <span className="current-label">当前</span>
            </li>
            <li>
              <span className="timeline-dot">
                <Circle size={9} />
              </span>
              <div>
                <h3>Phase 2 · 项目制作结构</h3>
                <p>建立 Project → Script → Scene → Shot</p>
              </div>
            </li>
          </ol>
        </section>
        <section className="principles panel">
          <span className="principles-icon">
            <HardDrive size={22} />
          </span>
          <h2>你的工作台，你的数据。</h2>
          <p>
            核心数据保存在本机。未来导入的图片、视频将复制到工作空间，集中管理。
          </p>
          <div className="principle-line">
            <Check size={14} /> 本地优先，无需注册
          </div>
          <div className="principle-line">
            <Check size={14} /> 外部生成，工作台内组织
          </div>
          <div className="principle-line">
            <Check size={14} /> 按阶段完善，保持清晰边界
          </div>
          <a
            href="/api/docs"
            target="_blank"
            rel="noreferrer"
            className="docs-link"
          >
            查看本地 API 文档 <ExternalLink size={13} />
          </a>
        </section>
      </div>
      <div className="phase-note">
        <ArrowDown size={14} />
        <span>数据与文件基础设施已建立，项目与素材管理将在后续阶段开放。</span>
      </div>
    </div>
  );
}
