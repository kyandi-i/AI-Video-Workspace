import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Users } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/common/page-header";
import { QueryState, QueryErrors } from "@/components/common/query-state";
import { EmptyState } from "@/components/common/empty-state";
import { MediaCard } from "@/components/common/media-card";
import { assetApi } from "@/features/assets/api";
import { useCharacters, useCharacterActions } from "./hooks";
import { CharacterEditor } from "./components";
import { characterApi } from "./api";
export function Component() {
  const { projectId = "" } = useParams();
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [deleted, setDeleted] = useState(false);
  const [error, setError] = useState("");
  const query = useCharacters(projectId, search, deleted);
  const actions = useCharacterActions(projectId);
  return (
    <div className="workspace-page characters-page">
      <PageHeader
        title="Characters"
        description="角色身份、视觉状态与参考素材"
        actions={<CharacterEditor project={projectId} />}
      />
      <div className="asset-inline-form">
        <Input
          type="search"
          aria-label="搜索角色"
          placeholder="Search name or description…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <Button
          variant="secondary"
          aria-pressed={deleted}
          onClick={() => setDeleted(!deleted)}
        >
          {deleted ? "隐藏已删除" : "显示已删除"}
        </Button>
      </div>
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      {!query.data ? (
        <QueryState queries={[query]} />
      ) : (
        <>
          <QueryErrors queries={[query]} />
          {!query.data.length && (
            <EmptyState
              icon={Users}
              title={search ? "没有匹配的角色" : "No characters yet"}
              description="Create your first character，随后建立视觉状态并绑定参考素材。"
            />
          )}
          <div className="asset-grid">
            {query.data.map((character) => {
              const image = character.assets.find(
                (asset) => asset.asset_type === "IMAGE",
              );
              return (
                <div key={character.id} className="character-card">
                  <MediaCard
                    name={character.name}
                    src={image ? assetApi.thumbnail(image.id) : undefined}
                    mediaType={character.deleted_at ? "已删除" : "Character"}
                    metadata={
                      <>
                        <span>
                          {character.state_count} states ·{" "}
                          {character.asset_count} references
                        </span>
                        <span>
                          {new Date(character.updated_at).toLocaleString()}
                        </span>
                      </>
                    }
                    onSelect={
                      character.deleted_at
                        ? undefined
                        : () =>
                            navigate(
                              `/projects/${projectId}/characters/${character.id}`,
                            )
                    }
                  />
                  {character.deleted_at && (
                    <Button
                      variant="secondary"
                      disabled={actions.isPending}
                      onClick={async () => {
                        try {
                          await actions.run(() =>
                            characterApi.restore("characters", character.id),
                          );
                        } catch (e) {
                          setError(e instanceof Error ? e.message : "恢复失败");
                        }
                      }}
                    >
                      恢复 {character.name}
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
