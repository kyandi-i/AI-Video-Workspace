import { StatusBadge } from "@/components/common/status-badge";
import { useState } from "react";
import { Folder, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input, SearchInput } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { WorkspacePanel } from "@/components/common/workspace-panel";
import { PageHeader } from "@/components/common/page-header";
import { MediaCard } from "@/components/common/media-card";
import { EntityCard } from "@/components/common/entity-card";
import { EmptyState } from "@/components/common/empty-state";
import { DetailSheet } from "@/components/common/detail-sheet";
import { notify } from "@/lib/notifications";
import { useTheme } from "@/lib/theme";

// Development-only interaction fixtures; never included in the production route tree.
export function Component() {
  const { theme, setTheme } = useTheme();
  const [sheet, setSheet] = useState(false);
  const [selected, setSelected] = useState(false);
  return (
    <div className="ui-preview">
      <PageHeader
        title="UI Foundation 验收页"
        description="仅开发环境可见。以下为组件交互样例，不代表业务数据。"
        actions={
          <Button onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
            切换主题
          </Button>
        }
      />
      <WorkspacePanel title="按钮与状态">
        <div className="preview-row">
          <Button>Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="destructive">Destructive</Button>
          <Button size="icon" aria-label="添加示例">
            <Plus />
          </Button>
          <Button disabled>Disabled</Button>
        </div>
        <div className="preview-row">
          {(["neutral", "accent", "success", "warning", "danger"] as const).map(
            (tone) => (
              <Badge key={tone} tone={tone}>
                {tone}
              </Badge>
            ),
          )}
        </div>
      </WorkspacePanel>
      <div className="preview-grid">
        <WorkspacePanel title="表单控件">
          <div className="preview-fields">
            <label>
              名称
              <Input placeholder="输入名称" />
            </label>
            <label>
              搜索
              <SearchInput placeholder="搜索内容" />
            </label>
            <label>
              说明
              <Textarea placeholder="输入说明" />
            </label>
            <label>
              比例
              <Select defaultValue="wide">
                <SelectTrigger aria-label="比例">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="wide">16:9</SelectItem>
                  <SelectItem value="square">1:1</SelectItem>
                  <SelectItem value="portrait">3:4</SelectItem>
                </SelectContent>
              </Select>
            </label>
            <label>
              只读
              <Input value="Read only" readOnly />
            </label>
            <Input aria-label="禁用输入" disabled placeholder="Disabled" />
            <div className="preview-row">
              <Checkbox id="preview-check" />
              <label htmlFor="preview-check">选择样例</label>
              <Switch id="preview-switch" />
              <label htmlFor="preview-switch">启用样例</label>
            </div>
          </div>
        </WorkspacePanel>
        <WorkspacePanel title="标签与反馈">
          <Tabs defaultValue="one">
            <TabsList>
              <TabsTrigger value="one">面板一</TabsTrigger>
              <TabsTrigger value="two">面板二</TabsTrigger>
            </TabsList>
            <TabsContent value="one">
              <EmptyState
                compact
                icon={Folder}
                title="暂无内容"
                description="空状态组件示例"
                action={
                  <Button
                    size="sm"
                    onClick={() => notify.info("空状态操作已触发")}
                  >
                    示例操作
                  </Button>
                }
              />
            </TabsContent>
            <TabsContent value="two">第二个面板内容</TabsContent>
          </Tabs>
          <Separator />
          <div className="preview-row">
            <Button
              variant="secondary"
              onClick={() => notify.success("保存成功示例")}
            >
              Success toast
            </Button>
            <Button
              variant="secondary"
              onClick={() => notify.error("错误反馈示例")}
            >
              Error toast
            </Button>
            <Button
              variant="secondary"
              onClick={() => notify.info("提示信息示例")}
            >
              Info toast
            </Button>
          </div>
          <Skeleton className="skeleton-block" />
        </WorkspacePanel>
        <WorkspacePanel title="弹层">
          <div className="preview-row">
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="secondary">打开 Dialog</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>对话框样例</DialogTitle>
                  <DialogDescription>
                    验证键盘焦点与关闭行为。
                  </DialogDescription>
                </DialogHeader>
                <Input aria-label="对话框输入" />
                <DialogFooter>
                  <DialogClose asChild>
                    <Button>完成</Button>
                  </DialogClose>
                </DialogFooter>
              </DialogContent>
            </Dialog>
            <Button variant="secondary" onClick={() => setSheet(true)}>
              打开 DetailSheet
            </Button>
          </div>
          <EntityCard
            name="EntityCard 样式样例"
            metadata="通用实体容器"
            status={<StatusBadge status="DRAFT" />}
          />
        </WorkspacePanel>
      </div>
      <WorkspacePanel
        title="媒体比例与选择"
        description="无远程资源；仅展示媒体占位、布局与选择状态。"
      >
        <div className="preview-grid">
          <MediaCard
            name="16:9 容器"
            mediaType="IMAGE"
            aspectRatio="16/9"
            metadata="Cover · 横版"
            selected={selected}
            onSelect={() => setSelected(!selected)}
          />
          <MediaCard
            name="1:1 容器"
            mediaType="IMAGE"
            aspectRatio="1/1"
            metadata="Contain · 方形"
            fit="contain"
          />
          <MediaCard
            name="3:4 容器"
            mediaType="IMAGE"
            aspectRatio="3/4"
            metadata="Cover · 竖版"
          />
        </div>
      </WorkspacePanel>
      <DetailSheet
        open={sheet}
        onOpenChange={setSheet}
        title="详情面板样例"
        description="右侧详情布局、预览与滚动。"
        preview={
          <div className="workspace-preview">
            <Folder size={32} />
            预览区
          </div>
        }
        actions={<Button onClick={() => setSheet(false)}>完成预览</Button>}
      >
        {Array.from({ length: 12 }, (_, index) => (
          <p key={index}>Metadata {index + 1} · 组件布局验收</p>
        ))}
      </DetailSheet>
    </div>
  );
}
