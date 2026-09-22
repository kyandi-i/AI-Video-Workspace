import { useState } from "react";
import { Button } from "@/components/ui/button";
import { EntityForm, type Field } from "@/components/common/entity-form";
import { AssetPicker } from "@/features/assets/asset-picker";
import { ImportAssets } from "@/features/assets/import-assets";
import { AssetDetailSheet } from "@/features/assets/asset-detail";
import { assetApi } from "@/features/assets/api";
import type { Asset } from "@/features/assets/types";
import { characterApi } from "./api";
import { useCharacterActions } from "./hooks";
import type { Character, CharacterState, OwnerKind } from "./types";
const fields: Field[] = [
  { name: "name", label: "名称", required: true, maxLength: 255 },
  { name: "description", label: "描述", kind: "textarea" },
];
export function CharacterEditor({
  project,
  character,
  state,
  characterId,
}: {
  project: string;
  character?: Character;
  state?: CharacterState;
  characterId?: string;
}) {
  const actions = useCharacterActions(project);
  const isState = Boolean(characterId);
  const entity = isState ? state : character;
  const title = `${entity ? "编辑" : "创建"}${isState ? "角色状态" : "角色"}`;
  return (
    <EntityForm
      title={title}
      trigger={
        <Button variant={entity ? "secondary" : "default"}>{title}</Button>
      }
      fields={
        isState
          ? fields
          : [
              ...fields,
              { name: "notes", label: "长期约束 / 备注", kind: "textarea" },
            ]
      }
      initial={{
        name: entity?.name ?? "",
        description: entity?.description ?? "",
        ...(!isState ? { notes: character?.notes ?? "" } : {}),
      }}
      onSave={(values) =>
        actions.run(() =>
          entity
            ? characterApi.update(
                isState ? "character-states" : "characters",
                entity.id,
                values,
              )
            : isState
              ? characterApi.createState(characterId!, values)
              : characterApi.create(project, values),
        )
      }
    />
  );
}
export function AssetReferences({
  project,
  kind,
  id,
  assets,
}: {
  project: string;
  kind: OwnerKind;
  id: string;
  assets: Asset[];
}) {
  const actions = useCharacterActions(project);
  const [importing, setImporting] = useState(false);
  const [preview, setPreview] = useState("");
  const [error, setError] = useState("");
  const bind = (assetId: string) =>
    actions.run(() => characterApi.asset(kind, id, assetId));
  return (
    <div className="character-references">
      <div className="row-actions">
        <AssetPicker bound={assets} onConfirm={bind} />
        <Button variant="ghost" onClick={() => setImporting(!importing)}>
          {importing ? "收起导入" : "Import Asset"}
        </Button>
      </div>
      {importing && <ImportAssets onImported={(asset) => bind(asset.id)} />}
      {!assets.length && (
        <p className="muted-copy">尚无参考资产，请绑定已有素材或导入。</p>
      )}
      <div className="reference-strip">
        {assets.map((asset) => (
          <div key={asset.id} className="reference-item">
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
              disabled={actions.isPending}
              aria-label={`解绑 ${asset.name}`}
              onClick={async () => {
                setError("");
                try {
                  await actions.run(() =>
                    characterApi.asset(kind, id, asset.id, true),
                  );
                } catch (e) {
                  setError(e instanceof Error ? e.message : "解绑失败");
                }
              }}
            >
              解绑
            </Button>
          </div>
        ))}
      </div>
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      {preview && (
        <AssetDetailSheet id={preview} onClose={() => setPreview("")} />
      )}
    </div>
  );
}
