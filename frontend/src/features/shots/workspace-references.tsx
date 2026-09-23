import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { WorkspacePanel } from "@/components/common/workspace-panel";
import { Button } from "@/components/ui/button";
import { AssetPicker } from "@/features/assets/asset-picker";
import { ImportAssets } from "@/features/assets/import-assets";
import { AssetDetailSheet } from "@/features/assets/asset-detail";
import { assetApi } from "@/features/assets/api";
import type { Asset } from "@/features/assets/types";

export function WorkspaceReferences({
  shotId,
  assets,
}: {
  shotId: string;
  assets: Asset[];
}) {
  const [preview, setPreview] = useState("");
  const [all, setAll] = useState(false);
  const [importing, setImporting] = useState(false);
  const client = useQueryClient();
  const bind = useMutation({
    mutationFn: ({ id, remove = false }: { id: string; remove?: boolean }) =>
      assetApi.bind(id, "shots", shotId, remove),
    onSuccess: async () => {
      await Promise.all([
        client.invalidateQueries({ queryKey: ["shot-workspace", shotId] }),
        client.invalidateQueries({ queryKey: ["assets"] }),
      ]);
    },
  });
  return (
    <WorkspacePanel
      title="Reference Assets"
      description="镜头参考素材 · 解绑仅解除关系"
      metadata={`${assets.length}`}
    >
      <div className="row-actions">
        <AssetPicker
          bound={assets}
          onConfirm={(id) => bind.mutateAsync({ id })}
        />
        <Button variant="secondary" onClick={() => setImporting(!importing)}>
          Import Asset
        </Button>
      </div>
      {importing && (
        <ImportAssets
          onImported={(asset) => bind.mutateAsync({ id: asset.id })}
        />
      )}
      {!assets.length && (
        <p className="muted-copy">
          No reference assets · Bind Asset or Import Asset
        </p>
      )}
      <div className="reference-strip">
        {(all ? assets : assets.slice(0, 6)).map((asset) => (
          <div className="reference-item" key={asset.id}>
            <button title={asset.name} onClick={() => setPreview(asset.id)}>
              <img
                src={assetApi.thumbnail(asset.id)}
                alt={asset.name}
                loading="lazy"
              />
              <span>{asset.name}</span>
            </button>
            <Button
              size="sm"
              variant="ghost"
              disabled={bind.isPending}
              onClick={() => bind.mutate({ id: asset.id, remove: true })}
              aria-label={`Unbind ${asset.name}`}
            >
              Unbind
            </Button>
          </div>
        ))}
      </div>
      {assets.length > 6 && (
        <Button variant="ghost" onClick={() => setAll(!all)}>
          {all ? "Show Less" : `View All (${assets.length})`}
        </Button>
      )}
      {bind.error && (
        <p role="alert" className="error-banner">
          {bind.error.message}
        </p>
      )}
      {preview && (
        <AssetDetailSheet id={preview} onClose={() => setPreview("")} />
      )}
    </WorkspacePanel>
  );
}
