import { useEffect, useRef, useState } from "react";
import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import "../recycle-bin/recycle-bin.css";

export function ProjectExport({ projectId }: { projectId: string }) {
  const busy = useRef(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [ready, setReady] = useState<{ url: string; name: string }>();
  useEffect(() => () => { if (ready) URL.revokeObjectURL(ready.url); }, [ready]);
  async function prepare() {
    if (busy.current) return;
    busy.current = true;
    setPending(true);
    setError("");
    try {
      const response = await fetch(`/api/projects/${projectId}/export`, { method: "POST" });
      if (!response.ok) {
        const body = await response.json();
        throw new Error(body.message || "导出失败，请重试。");
      }
      const blob = await response.blob();
      const encoded = response.headers.get("Content-Disposition")?.match(/filename\*=UTF-8''([^;]+)/)?.[1];
      const next = { url: URL.createObjectURL(blob), name: encoded ? decodeURIComponent(encoded) : "project.zip" };
      setReady(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "无法连接本地服务，请重试。");
    } finally {
      busy.current = false;
      setPending(false);
    }
  }
  return <div className="project-export">
    <Button variant="secondary" disabled={pending} onClick={() => void prepare()}><Download />{pending ? "Exporting…" : "Export Project"}</Button>
    {ready && <a href={ready.url} download={ready.name}>Download ZIP</a>}
    {error && <p role="alert">{error}</p>}
    {pending && <span role="status">正在打包项目与媒体…</span>}
  </div>;
}
