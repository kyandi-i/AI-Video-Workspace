import { useState } from "react";
import { Link } from "react-router-dom";
import { useProjects } from "@/features/projects/hooks";
import { QueryState } from "@/components/common/query-state";
import {
  Activity,
  ArrowUpRight,
  Check,
  Database,
  FolderOpen,
  HardDrive,
  Images,
  RefreshCw,
  ScanLine,
  MoreHorizontal,
  Folder,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/common/page-header";
import { WorkspacePanel } from "@/components/common/workspace-panel";
import { EmptyState } from "@/components/common/empty-state";
import { WorkspaceInfo } from "@/features/settings/workspace-info";
import { useWorkspace } from "@/features/settings/use-workspace";
import { useHealth } from "./use-health";

export function DashboardPage() {
  const projects = useProjects();
  const health = useHealth();
  const workspace = useWorkspace();
  const [details, setDetails] = useState(false);
  const ready = health.isSuccess && !health.isError;
  const storageReady = workspace.isSuccess && workspace.data.initialized;
  return (
    <div className="workspace-page">
      <PageHeader
        title="工作空间概览"
        description="项目、素材与镜头制作的统一工作空间。"
        metadata={<Badge>Overview</Badge>}
        actions={
          <>
            <Button
              variant="secondary"
              size="icon"
              aria-label="重新检查连接"
              disabled={health.isFetching || workspace.isFetching}
              onClick={() => {
                void health.refetch();
                void workspace.refetch();
              }}
            >
              <RefreshCw className={health.isFetching ? "spin" : ""} />
            </Button>
            <Button onClick={() => setDetails(true)}>
              <Folder size={15} />
              工作空间信息
            </Button>
          </>
        }
      />
      {health.isError && (
        <div role="alert" className="error-banner">
          <Activity size={16} />
          <span>
            本地服务连接中断。{health.error.message}。恢复后将自动重连。
          </span>
        </div>
      )}
      <section className="status-strip" aria-label="工作空间状态">
        <div>
          <span className="status-label">
            <HardDrive size={15} />
            本地服务
          </span>
          <strong>
            {health.isPending ? (
              <Skeleton className="skeleton-status" />
            ) : ready ? (
              <>
                <span className="online-dot" />
                连接正常
              </>
            ) : (
              "无法连接"
            )}
          </strong>
          <span className="status-caption">仅在本机运行</span>
        </div>
        <div>
          <span className="status-label">
            <Database size={15} />
            数据存储
          </span>
          <strong>
            {health.isPending ? (
              <Skeleton className="skeleton-status" />
            ) : ready && health.data.storage_initialized ? (
              "已初始化"
            ) : (
              "等待服务确认"
            )}
          </strong>
          <span className="status-caption">数据库与文件独立保存</span>
        </div>
        <div>
          <span className="status-label">
            <ScanLine size={15} />
            制作方式
          </span>
          <strong>本地管理 · 外部生成</strong>
          <span className="status-caption">围绕每一个镜头组织内容</span>
        </div>
      </section>
      <div className="dashboard-grid">
        <div className="dashboard-main">
          <WorkspacePanel
            title="最近项目"
            metadata="Projects"
            actions={
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" aria-label="项目面板选项">
                    <MoreHorizontal />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onSelect={() => setDetails(true)}>
                    查看工作空间信息
                    <ArrowUpRight size={14} />
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            }
          >
            <Tabs defaultValue="recent">
              <TabsList aria-label="项目显示范围">
                <TabsTrigger value="recent">最近更新</TabsTrigger>
                <TabsTrigger value="all">全部项目</TabsTrigger>
              </TabsList>
              <TabsContent value="recent">
                {projects.isPending || projects.isError ? (
                  <QueryState queries={[projects]} />
                ) : projects.data.length ? (
                  <div className="dashboard-projects">
                    {[...projects.data]
                      .sort((a, b) => b.updated_at.localeCompare(a.updated_at))
                      .slice(0, 5)
                      .map((project) => (
                        <Link key={project.id} to={`/projects/${project.id}`}>
                          <FolderOpen size={16} />
                          <strong>{project.name}</strong>
                          <Badge>{project.status}</Badge>
                          <ArrowUpRight size={14} />
                        </Link>
                      ))}
                  </div>
                ) : (
                  <EmptyState
                    icon={FolderOpen}
                    title="尚无可展示的项目"
                    description="创建项目，开始组织剧本与镜头。"
                    action={
                      <Button asChild>
                        <Link to="/projects">打开 Projects</Link>
                      </Button>
                    }
                  />
                )}
              </TabsContent>
              <TabsContent value="all">
                <Button asChild variant="secondary">
                  <Link to="/projects">查看全部项目</Link>
                </Button>
              </TabsContent>
            </Tabs>
          </WorkspacePanel>
          <div className="dashboard-secondary">
            <WorkspacePanel title="最近镜头" metadata="Shots">
              <EmptyState
                compact
                icon={ScanLine}
                title="按项目查看镜头"
                description="打开项目中的 Shots，查看、筛选和编辑镜头。"
                action={
                  <Button asChild variant="secondary" size="sm">
                    <Link to="/projects">选择项目</Link>
                  </Button>
                }
              />
            </WorkspacePanel>
            <WorkspacePanel title="最近素材" metadata="Assets">
              <EmptyState
                compact
                icon={Images}
                title="暂无素材预览"
                description="素材与引用内容将在这里集中展示。"
              />
            </WorkspacePanel>
          </div>
        </div>
        <div className="dashboard-aside">
          <WorkspacePanel
            title="本地工作空间"
            actions={
              <Badge tone={storageReady ? "success" : "neutral"}>
                {storageReady ? "Ready" : "Local"}
              </Badge>
            }
          >
            <div className="storage-summary">
              <div className="storage-mark">
                <HardDrive size={24} strokeWidth={1.4} />
              </div>
              <div>
                <strong>Managed local storage</strong>
                <span>文件与数据库保存在你的设备</span>
              </div>
            </div>
            <div className="storage-path">
              <span>WORKSPACE ROOT</span>
              {workspace.isPending ? (
                <Skeleton className="skeleton-line" />
              ) : workspace.isError ? (
                <div className="inline-error" role="alert">
                  暂时无法读取路径
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => void workspace.refetch()}
                  >
                    重试
                  </Button>
                </div>
              ) : (
                <code>{workspace.data.workspace_root}</code>
              )}
            </div>
            <dl className="storage-facts">
              <div>
                <dt>数据库</dt>
                <dd>
                  {workspace.isSuccess && workspace.data.initialized ? (
                    <>
                      <Check size={13} />
                      已就绪
                    </>
                  ) : (
                    "等待确认"
                  )}
                </dd>
              </div>
              <div>
                <dt>存储策略</dt>
                <dd>托管本地副本</dd>
              </div>
              <div>
                <dt>同步方式</dt>
                <dd>仅本地</dd>
              </div>
            </dl>
            <Button
              variant="ghost"
              className="panel-link"
              onClick={() => setDetails(true)}
            >
              查看存储信息
              <ArrowUpRight />
            </Button>
          </WorkspacePanel>
          <WorkspacePanel title="最近活动" metadata="Activity">
            <EmptyState
              compact
              icon={Activity}
              title="暂无活动记录"
              description="工作空间中的操作记录将在这里显示。"
            />
          </WorkspacePanel>
          <div className="privacy-note">
            <HardDrive size={15} />
            <div>
              <strong>本地优先</strong>
              <p>素材由你保管，工作空间无需登录。</p>
            </div>
          </div>
        </div>
      </div>
      <WorkspaceInfo open={details} onOpenChange={setDetails} />
    </div>
  );
}
