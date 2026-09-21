import { Link, useParams, useSearchParams } from "react-router-dom";
import { Images, LayoutGrid, List } from "lucide-react";
import { PageHeader } from "@/components/common/page-header";
import { MediaCard } from "@/components/common/media-card";
import { QueryState, QueryErrors } from "@/components/common/query-state";
import { EmptyState } from "@/components/common/empty-state";
import { Choice } from "@/components/common/entity-form";
import { SearchInput } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAssets, useTags } from "./hooks";
import { ImportAssets } from "./import-assets";
import { AssetDetailSheet } from "./asset-detail";
import {
  assetTypeOptions,
  assetDisplay,
  dimensions,
  sizeLabel,
} from "./display";
import { assetApi } from "./api";
import type { Asset } from "./types";

function Tags({ asset }: { asset: Asset }) {
  return (
    <span className="asset-tag-summary">
      {asset.tags.slice(0, 3).map((tag) => (
        <Badge key={tag.id} title={tag.name}>
          {tag.name}
        </Badge>
      ))}
      {asset.tags.length > 3 && <span>+{asset.tags.length - 3}</span>}
    </span>
  );
}
export function Component() {
  const { projectId } = useParams();
  const [params, setParams] = useSearchParams();
  const search = params.get("q") ?? "";
  const type = params.get("type") ?? "all";
  const tag = params.get("tag") ?? "all";
  const shotId = params.get("shot_id") ?? undefined;
  const view = params.get("view") === "list" ? "list" : "grid";
  const selected = params.get("asset");
  const filters = {
    ...(search ? { search } : {}),
    ...(type !== "all" ? { asset_type: type } : {}),
    ...(tag !== "all" ? { tag_id: tag } : {}),
    ...(projectId ? { project_id: projectId } : {}),
    ...(shotId ? { shot_id: shotId } : {}),
  };
  const query = useAssets(filters);
  const tags = useTags();
  function change(key: string, value: string) {
    setParams(
      (current) => {
        const next = new URLSearchParams(current);
        if (!value || value === "all") next.delete(key);
        else next.set(key, value);
        return next;
      },
      { replace: true },
    );
  }
  const assets = query.data?.pages.flat() ?? [];
  const filtered = search || type !== "all" || tag !== "all";
  return (
    <div
      className={
        projectId
          ? "workflow-stack asset-library"
          : "workspace-page workflow-stack asset-library"
      }
    >
      <PageHeader
        title={projectId ? "Project Assets" : "Asset Library"}
        description={
          projectId || shotId
            ? "查看已绑定素材；在全局资产库详情中建立或解除关联。"
            : "统一管理图片与视频，复用到项目和镜头。"
        }
        actions={
          <div className="asset-view-toggle" aria-label="视图">
            <Button
              variant="secondary"
              size="icon"
              aria-label="Grid View"
              aria-pressed={view === "grid"}
              onClick={() => change("view", "grid")}
            >
              <LayoutGrid />
            </Button>
            <Button
              variant="secondary"
              size="icon"
              aria-label="List View"
              aria-pressed={view === "list"}
              onClick={() => change("view", "list")}
            >
              <List />
            </Button>
          </div>
        }
      />
      {projectId || shotId ? (
        <Button asChild variant="secondary">
          <Link to="/assets">打开全局 Asset Library</Link>
        </Button>
      ) : (
        <ImportAssets />
      )}
      <div className="asset-filters">
        <SearchInput
          aria-label="搜索资产"
          placeholder="搜索名称或原始文件名…"
          value={search}
          onChange={(event) => change("q", event.target.value)}
        />
        <Choice
          label="资产类型筛选"
          value={type}
          onChange={(value) => change("type", value)}
          options={[{ value: "all", label: "All Types" }, ...assetTypeOptions]}
        />
        <Choice
          label="标签筛选"
          value={tag}
          disabled={!tags.data}
          onChange={(value) => change("tag", value)}
          options={[
            { value: "all", label: "All Tags" },
            ...(tags.data ?? []).map((item) => ({
              value: item.id,
              label: item.name,
            })),
          ]}
        />
      </div>
      <QueryErrors queries={[tags]} />
      {!query.data ? (
        <QueryState queries={[query]} />
      ) : (
        <>
          <QueryErrors queries={[query]} />
          {!assets.length ? (
            <EmptyState
              icon={Images}
              title={filtered ? "没有匹配的资产" : "No assets yet"}
              description={
                filtered
                  ? "尝试其他名称或清除筛选。"
                  : projectId || shotId
                    ? "打开全局资产库，在资产详情中绑定项目或镜头。"
                    : "点击 Import Asset 或将文件拖入上方区域。"
              }
              action={
                filtered ? (
                  <Button
                    variant="secondary"
                    onClick={() =>
                      setParams((current) => {
                        const next = new URLSearchParams(current);
                        ["q", "type", "tag"].forEach((key) => next.delete(key));
                        return next;
                      })
                    }
                  >
                    清除筛选
                  </Button>
                ) : undefined
              }
            />
          ) : view === "grid" ? (
            <div className="asset-grid">
              {assets.map((asset) => (
                <MediaCard
                  key={asset.id}
                  name={asset.name}
                  src={assetApi.thumbnail(asset.id)}
                  mediaType={assetDisplay[asset.asset_type].label}
                  onSelect={() => change("asset", asset.id)}
                  selected={asset.id === selected}
                  metadata={
                    <>
                      <span>
                        {dimensions(asset)} · {sizeLabel(asset.file_size)}
                      </span>
                      <Tags asset={asset} />
                    </>
                  }
                />
              ))}
            </div>
          ) : (
            <div className="table-scroll">
              <table className="asset-table">
                <thead>
                  <tr>
                    <th>名称</th>
                    <th>类型</th>
                    <th>大小</th>
                    <th>尺寸 / 时长</th>
                    <th>Tags</th>
                    <th>更新时间</th>
                  </tr>
                </thead>
                <tbody>
                  {assets.map((asset) => (
                    <tr key={asset.id}>
                      <td>
                        <button
                          className="asset-row-open"
                          onClick={() => change("asset", asset.id)}
                        >
                          <img
                            src={assetApi.thumbnail(asset.id)}
                            alt=""
                            loading="lazy"
                          />
                          <span title={asset.name}>{asset.name}</span>
                        </button>
                      </td>
                      <td>
                        <Badge tone={assetDisplay[asset.asset_type].tone}>
                          {assetDisplay[asset.asset_type].label}
                        </Badge>
                      </td>
                      <td>{sizeLabel(asset.file_size)}</td>
                      <td>{dimensions(asset)}</td>
                      <td>
                        <Tags asset={asset} />
                      </td>
                      <td>{new Date(asset.updated_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {query.hasNextPage && (
            <Button
              variant="secondary"
              disabled={query.isFetchingNextPage}
              onClick={() => void query.fetchNextPage()}
            >
              {query.isFetchingNextPage ? "加载中…" : "加载更多"}
            </Button>
          )}
        </>
      )}
      {selected && (
        <AssetDetailSheet
          key={selected}
          id={selected}
          onClose={() => change("asset", "")}
        />
      )}
    </div>
  );
}
