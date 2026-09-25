import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { requestJson } from "@/api/client";
import { WorkspacePanel } from "@/components/common/workspace-panel";
import { QueryState } from "@/components/common/query-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { promptApi, type ProviderSettings } from "@/features/prompts/api";

function SettingsForm({ initial }: { initial: ProviderSettings }) {
  const client = useQueryClient();
  const [url, setUrl] = useState(initial.api_base_url);
  const [model, setModel] = useState(initial.model);
  const [key, setKey] = useState("");
  const [clear, setClear] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  return (
    <form
      className="space-y-3"
      onSubmit={async (e) => {
        e.preventDefault();
        if (pending) return;
        setPending(true);
        setError("");
        setSaved(false);
        try {
          const data = await requestJson<ProviderSettings>(
            "/settings/ai",
            "PUT",
            {
              api_base_url: url,
              model,
              ...(clear ? { api_key: "" } : key ? { api_key: key } : {}),
            },
          );
          setKey("");
          setClear(false);
          setSaved(true);
          client.setQueryData(["ai-settings"], data);
        } catch (err) {
          setError(err instanceof Error ? err.message : "配置保存失败");
        } finally {
          setPending(false);
        }
      }}
    >
      <fieldset disabled={pending} className="space-y-3">
        <label htmlFor="ai-base-url">API Base URL</label>
        <Input
          id="ai-base-url"
          type="url"
          value={url}
          required
          maxLength={2048}
          placeholder="https://your-provider.example/v1"
          onChange={(e) => {
            setUrl(e.target.value);
            setSaved(false);
          }}
        />
        <label htmlFor="ai-model">Model</label>
        <Input
          id="ai-model"
          value={model}
          required
          maxLength={255}
          onChange={(e) => {
            setModel(e.target.value);
            setSaved(false);
          }}
        />
        <label htmlFor="ai-key">API Key</label>
        <Input
          id="ai-key"
          type="password"
          autoComplete="new-password"
          value={key}
          maxLength={4096}
          placeholder={
            initial.api_key_configured ? "已配置 · 留空保留" : "尚未配置"
          }
          disabled={clear}
          onChange={(e) => {
            setKey(e.target.value);
            setSaved(false);
          }}
        />
        <p className="muted-copy">
          {initial.api_key_configured
            ? "API Key configured"
            : "API Key not configured"}
        </p>
        <label className="row-actions">
          <input
            type="checkbox"
            checked={clear}
            onChange={(e) => {
              setClear(e.target.checked);
              setKey("");
              setSaved(false);
            }}
          />
          清除已保存的 API Key
        </label>
        <p className="muted-copy">
          配置保存在本机，独立于项目数据。API Key 不会重新显示；留空保留原
          Key。Base URL 应包含 Provider 要求的路径（如 /v1）。
        </p>
        <Button type="submit" disabled={pending}>
          {pending ? "Saving AI Settings…" : "Save AI Settings"}
        </Button>
      </fieldset>
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      {saved && <p role="status">AI Settings saved</p>}
    </form>
  );
}

export function AISettings() {
  const query = useQuery({
    queryKey: ["ai-settings"],
    queryFn: promptApi.settings,
  });
  return (
    <WorkspacePanel
      title="AI Provider"
      description="OpenAI-compatible · 文本 Prompt"
    >
      {query.data ? (
        <SettingsForm initial={query.data} />
      ) : (
        <QueryState queries={[query]} />
      )}
    </WorkspacePanel>
  );
}
