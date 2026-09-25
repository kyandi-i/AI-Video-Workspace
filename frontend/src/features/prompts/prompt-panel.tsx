import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, LoaderCircle, Sparkles } from "lucide-react";
import { WorkspacePanel } from "@/components/common/workspace-panel";
import { QueryState } from "@/components/common/query-state";
import { Button } from "@/components/ui/button";
import { PromptTemplatePicker } from "@/features/templates/template-picker";
import type { Template } from "@/features/templates/api";
import { promptApi, type PromptPreview, type PromptRecord } from "./api";
import "./prompts.css";

function GenerateAction({
  shotId,
  preview,
  disabled,
}: {
  shotId: string;
  preview: PromptPreview;
  disabled: boolean;
}) {
  const [operationId] = useState(() => crypto.randomUUID());
  const busy = useRef(false);
  const client = useQueryClient();
  const generate = useMutation({
    mutationFn: () => promptApi.generate(shotId, preview, operationId),
    onSuccess: (record) =>
      client.setQueryData(["prompt-result", shotId], record),
  });
  return (
    <div className="space-y-3">
      <Button
        disabled={disabled || generate.isPending || generate.isSuccess}
        onClick={async () => {
          if (busy.current) return;
          busy.current = true;
          try {
            await generate.mutateAsync();
          } catch {
            /* Keep the operation id for Retry. */
          } finally {
            busy.current = false;
          }
        }}
      >
        {generate.isPending ? (
          <LoaderCircle className="animate-spin" />
        ) : (
          <Sparkles />
        )}
        {generate.isPending
          ? "Generating…"
          : generate.isError
            ? "Retry Generation"
            : "Generate"}
      </Button>
      {generate.isPending && (
        <p role="status">正在生成，请等待。离开页面后可返回查看已保存结果。</p>
      )}
      {generate.error && (
        <p role="alert" className="error-banner">
          {generate.error.message}
        </p>
      )}
      {generate.isSuccess && <p role="status">Generation saved</p>}
    </div>
  );
}

function GeneratedResult({ record }: { record: PromptRecord }) {
  const [copyStatus, setCopyStatus] = useState("");
  return (
    <div className="prompt-result">
      <div className="row-actions">
        <h3>Generated Prompt</h3>
        <Button
          variant="secondary"
          onClick={async () => {
            try {
              await navigator.clipboard.writeText(record.generated_content);
              setCopyStatus("Copied");
            } catch {
              setCopyStatus("复制失败，请选择文本手动复制。");
            }
          }}
        >
          <Copy />
          Copy Prompt
        </Button>
        <span role="status">{copyStatus}</span>
      </div>
      <p className="muted-copy">
        {record.template_name} · {record.model_name} ·{" "}
        {new Date(record.created_at).toLocaleString()}
      </p>
      <pre tabIndex={0} aria-label="Generated Prompt result">
        {record.generated_content}
      </pre>
      <details>
        <summary>本次生成使用的输入</summary>
        <pre>{record.rendered_input}</pre>
      </details>
    </div>
  );
}

export function PromptPanel({
  shotId,
  projectId,
  contextKey,
  dirty,
}: {
  shotId: string;
  projectId: string;
  contextKey: string;
  dirty: boolean;
}) {
  const [template, setTemplate] = useState<Template>();
  const preview = useQuery({
    queryKey: ["prompt-preview", shotId, template?.id, contextKey],
    queryFn: () => promptApi.preview(shotId, template!.id),
    enabled: Boolean(template) && !dirty,
    retry: false,
  });
  const result = useQuery({
    queryKey: ["prompt-result", shotId],
    queryFn: () => promptApi.latest(shotId),
    retry: false,
  });
  return (
    <WorkspacePanel
      title="Prompt"
      description="使用已保存的镜头上下文生成文本 Prompt。"
      className="prompt-panel"
    >
      <PromptTemplatePicker projectId={projectId} onSelect={setTemplate} />
      {template && <p className="muted-copy">Template: {template.name}</p>}
      <Link className="back-link" to="/settings">
        AI Provider Settings →
      </Link>
      {dirty && <p className="muted-copy">请先 Save Changes，再预览和生成。</p>}
      {template && !dirty && (
        <>
          {preview.data ? (
            <>
              <div className="row-actions">
                <h3>Actual Rendered Input</h3>
                <Button
                  variant="secondary"
                  disabled={preview.isFetching}
                  onClick={() => void preview.refetch()}
                >
                  Refresh Input
                </Button>
              </div>
              <pre tabIndex={0} aria-label="Actual Rendered Input">
                {preview.data.rendered_input}
              </pre>
              <details>
                <summary>Shot Context</summary>
                <pre>{preview.data.context.shot_context}</pre>
              </details>
              {preview.error && (
                <p role="alert" className="error-banner">
                  {preview.error.message}
                </p>
              )}
              <GenerateAction
                key={preview.data.input_hash}
                shotId={shotId}
                preview={preview.data}
                disabled={dirty || preview.isFetching || Boolean(preview.error)}
              />
            </>
          ) : (
            <QueryState queries={[preview]} />
          )}
        </>
      )}
      {result.error && <QueryState queries={[result]} />}
      {result.data && (
        <GeneratedResult key={result.data.id} record={result.data} />
      )}
    </WorkspacePanel>
  );
}
