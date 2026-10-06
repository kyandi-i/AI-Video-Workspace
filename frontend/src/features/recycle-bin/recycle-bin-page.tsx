import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RotateCcw, Trash2 } from "lucide-react";
import { requestJson } from "@/api/client";
import { PageHeader } from "@/components/common/page-header";
import { EmptyState } from "@/components/common/empty-state";
import { QueryState, QueryErrors } from "@/components/common/query-state";
import { Choice } from "@/components/common/entity-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import "./recycle-bin.css";

const types = [
  ["projects", "Project"], ["scripts", "Script"], ["scenes", "Scene"], ["shots", "Shot"],
  ["assets", "Asset"], ["characters", "Character"], ["character-states", "Character State"],
  ["prompt-templates", "Prompt Template"], ["storyboards", "Storyboard"], ["video-results", "Video Result"],
];
interface Item {
  entity_type: string; entity_id: string; display_name: string; deleted_at: string; context: string;
}
interface Page { items: Item[]; total: number }

export function Component() {
  const [type, setType] = useState("all");
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [notice, setNotice] = useState("");
  const client = useQueryClient();
  const query = useQuery({ queryKey: ["recycle-bin", type, search, offset], queryFn: () => {
    const params = new URLSearchParams({ search, offset: String(offset), limit: "100" });
    if (type !== "all") params.set("entity_type", type);
    return requestJson<Page>(`/recycle-bin?${params}`);
  } });
  const restore = useMutation({ mutationFn: (item: Item) => requestJson(`/${item.entity_type}/${item.entity_id}/restore`, "POST"),
    onSuccess: async (_, item) => {
      setNotice(`已恢复 ${item.display_name}`);
      await client.invalidateQueries();
    },
  });
  return <div className="workspace-page recycle-page">
    <PageHeader title="Recycle Bin" description="查看已删除记录并恢复。父级已删除时，请先恢复父级；恢复不会重新建立已解除的绑定。" />
    <div className="recycle-filters">
      <Choice label="Entity type" value={type} onChange={(value) => { setType(value); setOffset(0); }} options={[{ value: "all", label: "All types" }, ...types.map(([value, label]) => ({ value, label }))]} />
      <Input aria-label="Search deleted items" placeholder="搜索名称、编号或项目" value={search} onChange={(e) => { setSearch(e.target.value); setOffset(0); }} />
    </div>
    {notice && <p role="status">{notice}</p>}
    {restore.error && <p role="alert" className="error-banner">{restore.error.message} · 请检查父级、关联资产或来源后重试。</p>}
    {query.data && <QueryErrors queries={[query]} />}
    {!query.data ? <QueryState queries={[query]} /> : query.data.items.length === 0 ? <EmptyState icon={Trash2} title="No deleted items" description="当前筛选下没有可恢复的记录。" /> : <>
      <ul className="recycle-list" aria-label="Deleted items">
        {query.data.items.map((item) => <li key={`${item.entity_type}:${item.entity_id}`}>
          <div className="recycle-description">
            <span>{types.find(([value]) => value === item.entity_type)?.[1]}</span>
            <strong>{item.display_name}</strong>
            <p>{item.context}</p>
            <time dateTime={item.deleted_at}>{new Date(item.deleted_at).toLocaleString()}</time>
          </div>
          <Button variant="secondary" disabled={restore.isPending} aria-label={`Restore ${item.display_name}`} onClick={() => restore.mutate(item)}><RotateCcw />Restore</Button>
        </li>)}
      </ul>
    </>}
    {query.data && (offset > 0 || query.data.total > 100) && <div className="row-actions">
      <Button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 100))}>Previous page</Button>
      <span>{query.data.total} items</span>
      <Button disabled={offset + 100 >= query.data.total} onClick={() => setOffset(offset + 100)}>Next page</Button>
    </div>}
  </div>;
}
