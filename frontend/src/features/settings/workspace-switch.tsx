import { useState } from "react";
import { requestJson } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { notify } from "@/lib/notifications";

export function WorkspaceSwitch() {
  const [path, setPath] = useState("");
  const [pending, setPending] = useState(false);
  return (
    <form
      className="space-y-3"
      onSubmit={async (event) => {
        event.preventDefault();
        if (pending || !path.trim()) return;
        setPending(true);
        try {
          await requestJson("/settings/workspace", "PUT", {
            workspace_root: path.trim(),
          });
          // Discard every workspace-scoped query and any old detail route.
          window.location.assign("/settings");
        } catch (error) {
          notify.error(error instanceof Error ? error.message : "切换失败");
          setPending(false);
        }
      }}
    >
      <label htmlFor="workspace-root">新工作空间的绝对路径</label>
      <Input
        id="workspace-root"
        value={path}
        onChange={(event) => setPath(event.target.value)}
        disabled={pending}
        required
        aria-describedby="workspace-switch-help"
      />
      <p id="workspace-switch-help" className="text-sm text-muted-foreground">
        切换会打开目标目录；空目录将初始化为空工作空间，不会搬迁当前文件。
        迁移已有数据时，请先停止应用、完整复制工作空间并校验，再选择副本目录。
      </p>
      <Button type="submit" disabled={pending || !path.trim()}>
        {pending ? "正在切换…" : "保存并切换工作空间"}
      </Button>
    </form>
  );
}
