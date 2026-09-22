import { useRef, useState } from "react";
import { Upload, Check, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Choice } from "@/components/common/entity-form";
import { assetTypeOptions } from "./display";
import { useAssetActions } from "./hooks";
import type { Asset, AssetType } from "./types";

type ImportItem = {
  name: string;
  state: "waiting" | "working" | "done" | "error";
  message?: string;
};
export function ImportAssets({
  onImported,
}: { onImported?: (asset: Asset) => Promise<unknown> } = {}) {
  const input = useRef<HTMLInputElement>(null);
  const busy = useRef(false);
  const [pending, setPending] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [type, setType] = useState("auto");
  const [items, setItems] = useState<ImportItem[]>([]);
  const actions = useAssetActions();
  async function importFiles(files: File[]) {
    if (busy.current || !files.length) return;
    busy.current = true;
    setPending(true);
    setDragging(false);
    const entries: ImportItem[] = files.map((file) => ({
      name: file.name,
      state: "waiting",
    }));
    setItems([...entries]);
    try {
      for (const [index, file] of files.entries()) {
        entries[index] = { name: file.name, state: "working" };
        setItems([...entries]);
        try {
          if (file.size > 512 * 1024 * 1024)
            throw new Error("单个文件不能超过 512 MiB。");
          const imported = await actions.upload(
            file,
            type === "auto" ? undefined : (type as AssetType),
          );
          if (onImported) {
            try {
              await onImported(imported as Asset);
            } catch (cause) {
              throw new Error(
                `素材已导入 Asset Library，但绑定失败，请用 Bind Asset 重试。${cause instanceof Error ? cause.message : ""}`,
              );
            }
          }
          entries[index] = { name: file.name, state: "done" };
        } catch (error) {
          entries[index] = {
            name: file.name,
            state: "error",
            message:
              error instanceof Error ? error.message : "导入失败，请重试。",
          };
        }
        setItems([...entries]);
      }
    } finally {
      busy.current = false;
      setPending(false);
      if (input.current) input.current.value = "";
    }
  }
  return (
    <section
      className={`asset-import ${dragging ? "is-dragging" : ""}`}
      aria-label="导入资产区域"
      onDragOver={(event) => {
        event.preventDefault();
        if (!pending) setDragging(true);
      }}
      onDragLeave={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node))
          setDragging(false);
      }}
      onDrop={(event) => {
        event.preventDefault();
        void importFiles(Array.from(event.dataTransfer.files));
      }}
    >
      <div className="asset-import-bar">
        <Upload size={20} />
        <div>
          <strong>拖入图片或视频</strong>
          <p>PNG / JPEG / WebP · MP4 / MOV / WebM · 每个文件最多 512 MiB</p>
        </div>
        <Choice
          label="导入分类"
          value={type}
          onChange={setType}
          disabled={pending}
          options={[
            { value: "auto", label: "自动识别类型" },
            ...assetTypeOptions,
          ]}
        />
        <Button disabled={pending} onClick={() => input.current?.click()}>
          {pending ? "导入中…" : "Import Asset"}
        </Button>
        <input
          ref={input}
          className="sr-only"
          type="file"
          aria-label="选择资产文件"
          multiple
          accept=".png,.jpg,.jpeg,.webp,.mp4,.mov,.webm"
          disabled={pending}
          onChange={(event) =>
            void importFiles(Array.from(event.target.files ?? []))
          }
        />
      </div>
      {items.length > 0 && (
        <ul className="import-results" aria-live="polite">
          {items.map((item, index) => (
            <li
              key={index}
              className={item.state === "error" ? "field-error" : ""}
            >
              {item.state === "done" ? (
                <Check size={14} />
              ) : item.state === "error" ? (
                <AlertCircle size={14} />
              ) : (
                <Upload size={14} />
              )}
              <span title={item.name}>{item.name}</span>
              <span>
                {item.message ??
                  {
                    waiting: "等待导入",
                    working: "正在导入…",
                    done: "已导入",
                    error: "导入失败",
                  }[item.state]}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
