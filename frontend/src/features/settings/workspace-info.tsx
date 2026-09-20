import { Copy, Folder, HardDrive } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { DetailSheet } from "@/components/common/detail-sheet";
import { useWorkspace } from "./use-workspace";
import { notify } from "@/lib/notifications";

export function WorkspaceMetadata() {
  const workspace = useWorkspace();
  if (workspace.isPending)
    return (
      <div aria-label="正在读取工作空间" aria-busy="true">
        <Skeleton className="skeleton-line" />
        <Skeleton className="skeleton-line" />
      </div>
    );
  if (workspace.isError)
    return (
      <div className="inline-error" role="alert">
        <p>无法读取工作空间位置。</p>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => void workspace.refetch()}
        >
          重试
        </Button>
      </div>
    );
  return (
    <dl className="metadata-list">
      <div>
        <dt>工作空间目录</dt>
        <dd className="path-value">{workspace.data.workspace_root}</dd>
      </div>
      <div>
        <dt>数据库文件</dt>
        <dd className="path-value">{workspace.data.database_path}</dd>
      </div>
      <div>
        <dt>存储位置</dt>
        <dd>本机 · Managed Local Storage</dd>
      </div>
      <div>
        <dt>状态</dt>
        <dd>
          <Badge tone={workspace.data.initialized ? "success" : "warning"}>
            {workspace.data.initialized ? "已初始化" : "未初始化"}
          </Badge>
        </dd>
      </div>
    </dl>
  );
}

export function WorkspaceInfo({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (value: boolean) => void;
}) {
  const workspace = useWorkspace();
  async function copyPath() {
    if (!workspace.data) return;
    try {
      await navigator.clipboard.writeText(workspace.data.workspace_root);
      notify.success("工作空间路径已复制");
    } catch {
      notify.error("复制失败，请手动选择路径复制。");
    }
  }
  return (
    <DetailSheet
      open={open}
      onOpenChange={onOpenChange}
      title="工作空间信息"
      description="当前连接的本地目录与存储状态。"
      preview={
        <div className="workspace-preview">
          <Folder size={32} strokeWidth={1.3} />
          <span>Local workspace</span>
        </div>
      }
      actions={
        <Button
          variant="secondary"
          onClick={() => void copyPath()}
          disabled={!workspace.isSuccess}
        >
          <Copy />
          复制路径
        </Button>
      }
    >
      <WorkspaceMetadata />
      <div className="local-info">
        <HardDrive size={16} />
        <p>文件保存在本机。工作空间路径与原始素材位置相互独立。</p>
      </div>
    </DetailSheet>
  );
}
