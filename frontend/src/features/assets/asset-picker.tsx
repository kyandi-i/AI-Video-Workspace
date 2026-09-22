import { Users } from "lucide-react";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Choice } from "@/components/common/entity-form";
import { MediaCard } from "@/components/common/media-card";
import { QueryState, QueryErrors } from "@/components/common/query-state";
import { EmptyState } from "@/components/common/empty-state";
import { useAssets } from "./hooks";
import { assetApi } from "./api";
import { assetTypeOptions, assetDisplay } from "./display";
import type { Asset } from "./types";

function PickerContent({
  bound,
  onConfirm,
  close,
  pending,
  setPending,
}: {
  bound: Asset[];
  onConfirm: (id: string) => Promise<unknown>;
  close: () => void;
  pending: boolean;
  setPending: (v: boolean) => void;
}) {
  const [search, setSearch] = useState("");
  const [type, setType] = useState("all");
  const [selected, setSelected] = useState<Asset>();
  const [error, setError] = useState("");
  const busy = useRef(false);
  const query = useAssets({
    search,
    ...(type === "all" ? {} : { asset_type: type }),
  });
  const assets = query.data?.pages.flat() ?? [];
  return (
    <>
      <div className="form-body">
        <div className="asset-picker-filters">
          <Input
            type="search"
            aria-label="搜索已有资产"
            placeholder="Search assets…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            disabled={pending}
          />
          <Choice
            label="选择资产类型"
            value={type}
            onChange={setType}
            disabled={pending}
            options={[
              { value: "all", label: "All types" },
              ...assetTypeOptions,
            ]}
          />
        </div>
        {!query.data ? (
          <QueryState queries={[query]} />
        ) : (
          <>
            <QueryErrors queries={[query]} />
            {!assets.length && (
              <EmptyState
                icon={Users}
                compact
                title="没有匹配的资产"
                description="更改搜索或筛选条件，或先导入资产。"
              />
            )}
            <div className="asset-grid picker-grid">
              {assets.map((asset) => {
                const linked = bound.some((item) => item.id === asset.id);
                return (
                  <MediaCard
                    key={asset.id}
                    name={asset.name}
                    src={assetApi.thumbnail(asset.id)}
                    mediaType={assetDisplay[asset.asset_type].label}
                    metadata={
                      linked
                        ? "已绑定"
                        : selected?.id === asset.id
                          ? "已选择"
                          : "选择资产"
                    }
                    selected={selected?.id === asset.id || linked}
                    onSelect={() => {
                      if (!linked && !pending) setSelected(asset);
                    }}
                  />
                );
              })}
            </div>
            {query.hasNextPage && (
              <Button
                variant="secondary"
                disabled={query.isFetchingNextPage}
                onClick={() => void query.fetchNextPage()}
              >
                加载更多
              </Button>
            )}
          </>
        )}
        {selected && (
          <p className="asset-description">已选择：{selected.name}</p>
        )}
        {error && (
          <p role="alert" className="error-banner">
            {error}
          </p>
        )}
      </div>
      <DialogFooter>
        <Button variant="secondary" disabled={pending} onClick={close}>
          取消
        </Button>
        <Button
          disabled={!selected || pending}
          onClick={async () => {
            if (!selected || busy.current) return;
            busy.current = true;
            setPending(true);
            setError("");
            try {
              await onConfirm(selected.id);
              close();
            } catch (e) {
              setError(e instanceof Error ? e.message : "绑定失败");
            } finally {
              busy.current = false;
              setPending(false);
            }
          }}
        >
          {pending ? "绑定中…" : "确认绑定"}
        </Button>
      </DialogFooter>
    </>
  );
}
export function AssetPicker({
  bound,
  onConfirm,
}: {
  bound: Asset[];
  onConfirm: (id: string) => Promise<unknown>;
}) {
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState(false);
  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        if (!pending) setOpen(v);
      }}
    >
      <DialogTrigger asChild>
        <Button variant="secondary">Bind Asset</Button>
      </DialogTrigger>
      <DialogContent
        className="entity-dialog asset-picker"
        closeDisabled={pending}
        onInteractOutside={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>选择已有资产</DialogTitle>
          <DialogDescription>
            从统一 Asset Library 绑定参考素材。
          </DialogDescription>
        </DialogHeader>
        <PickerContent
          bound={bound}
          onConfirm={onConfirm}
          close={() => setOpen(false)}
          pending={pending}
          setPending={setPending}
        />
      </DialogContent>
    </Dialog>
  );
}
