import { Moon, Sun } from "lucide-react";
import { PageHeader } from "@/components/common/page-header";
import { WorkspacePanel } from "@/components/common/workspace-panel";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/lib/theme";
import { WorkspaceMetadata } from "./workspace-info";

export function SettingsPage() {
  const { theme, setTheme } = useTheme();
  return (
    <div className="workspace-page">
      <PageHeader title="设置" description="界面外观与当前工作空间信息。" />
      <div className="settings-grid">
        <WorkspacePanel
          title="界面外观"
          description="偏好仅保存在当前浏览器中。"
        >
          <div className="theme-choices">
            <Button
              variant={theme === "dark" ? "primary" : "secondary"}
              aria-pressed={theme === "dark"}
              onClick={() => setTheme("dark")}
            >
              <Moon />
              Dark
            </Button>
            <Button
              variant={theme === "light" ? "primary" : "secondary"}
              aria-pressed={theme === "light"}
              onClick={() => setTheme("light")}
            >
              <Sun />
              Light
            </Button>
          </div>
        </WorkspacePanel>
        <WorkspacePanel
          title="当前工作空间"
          description="当前目录与存储状态，仅供查看。"
        >
          <WorkspaceMetadata />
        </WorkspacePanel>
      </div>
    </div>
  );
}
