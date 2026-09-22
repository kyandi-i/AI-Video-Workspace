import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Users, ArrowUp, ArrowDown } from "lucide-react";
import { isMissingEntity } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/common/page-header";
import { WorkspacePanel } from "@/components/common/workspace-panel";
import { QueryState, QueryErrors } from "@/components/common/query-state";
import { EmptyState } from "@/components/common/empty-state";
import { DeleteEntity } from "@/components/common/entity-form";
import { assetApi } from "@/features/assets/api";
import { characterApi } from "./api";
import { useCharacter, useStates, useCharacterActions } from "./hooks";
import { CharacterEditor, AssetReferences } from "./components";
export function Component() {
  const { projectId = "", characterId = "" } = useParams();
  const navigate = useNavigate();
  const [deleted, setDeleted] = useState(false);
  const [error, setError] = useState("");
  const character = useCharacter(projectId, characterId);
  const states = useStates(projectId, characterId, deleted);
  const actions = useCharacterActions(projectId);
  async function run(action: () => Promise<unknown>) {
    setError("");
    try {
      await actions.run(action);
    } catch (e) {
      setError(e instanceof Error ? e.message : "操作失败");
    }
  }
  if (!character.data || isMissingEntity(character.error))
    return <QueryState queries={[character]} />;
  const entity = character.data;
  if (entity.project_id !== projectId)
    return (
      <EmptyState
        icon={Users}
        title="角色不属于此项目"
        description="请从项目 Characters 页面重新打开。"
      />
    );
  const active = states.data?.filter((state) => !state.deleted_at) ?? [];
  return (
    <div className="workspace-page character-detail">
      <Link className="back-link" to={`/projects/${projectId}/characters`}>
        ← Characters
      </Link>
      <QueryErrors queries={[character]} />
      <PageHeader
        title={entity.name}
        description={entity.description || "未填写描述"}
        actions={
          <div className="row-actions">
            <CharacterEditor project={projectId} character={entity} />
            <DeleteEntity
              name={entity.name}
              description="角色及其状态将被删除，所有参考资产与镜头绑定将解除；素材文件保留。"
              onDelete={async () => {
                await actions.run(() =>
                  characterApi.remove("characters", characterId),
                );
                navigate(`/projects/${projectId}/characters`);
              }}
            />
          </div>
        }
      />
      <WorkspacePanel title="Character Info">
        <p className="asset-description">
          {entity.notes || "未填写长期约束 / 备注"}
        </p>
      </WorkspacePanel>
      <WorkspacePanel title="Character Reference Assets">
        <AssetReferences
          project={projectId}
          kind="characters"
          id={characterId}
          assets={entity.assets}
        />
      </WorkspacePanel>
      <WorkspacePanel
        title="Character States"
        actions={
          <CharacterEditor project={projectId} characterId={characterId} />
        }
      >
        <Button
          variant="ghost"
          aria-pressed={deleted}
          onClick={() => setDeleted(!deleted)}
        >
          {deleted ? "隐藏已删除状态" : "显示已删除状态"}
        </Button>
        {error && (
          <p role="alert" className="error-banner">
            {error}
          </p>
        )}
        {!states.data ? (
          <QueryState queries={[states]} />
        ) : (
          <>
            <QueryErrors queries={[states]} />
            {!states.data.length && (
              <EmptyState
                icon={Users}
                compact
                title="No character states yet"
                description="创建角色在不同服装、装备或生产阶段的视觉状态。"
              />
            )}
            <div className="state-list">
              {states.data.map((state) => (
                <section
                  key={state.id}
                  className="state-card"
                  aria-label={state.name}
                >
                  <div className="state-heading">
                    <h3 title={state.name}>{state.name}</h3>
                    <Badge>{state.shot_usage_count} shots</Badge>
                    {state.deleted_at ? (
                      <Button
                        disabled={actions.isPending}
                        variant="secondary"
                        onClick={() =>
                          void run(() =>
                            characterApi.restore("character-states", state.id),
                          )
                        }
                      >
                        恢复状态
                      </Button>
                    ) : (
                      <div className="row-actions">
                        <Button
                          size="icon"
                          variant="ghost"
                          aria-label={`上移 ${state.name}`}
                          disabled={
                            actions.isPending || active[0]?.id === state.id
                          }
                          onClick={() =>
                            void run(() => characterApi.move(state.id, "up"))
                          }
                        >
                          <ArrowUp size={16} />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          aria-label={`下移 ${state.name}`}
                          disabled={
                            actions.isPending || active.at(-1)?.id === state.id
                          }
                          onClick={() =>
                            void run(() => characterApi.move(state.id, "down"))
                          }
                        >
                          <ArrowDown size={16} />
                        </Button>
                        <CharacterEditor
                          project={projectId}
                          characterId={characterId}
                          state={state}
                        />
                        <DeleteEntity
                          name={state.name}
                          description="使用中的状态需要先解除镜头绑定。删除后参考资产本体保留。"
                          onDelete={() =>
                            actions.run(() =>
                              characterApi.remove("character-states", state.id),
                            )
                          }
                        />
                      </div>
                    )}
                  </div>
                  <p className="asset-description">
                    {state.description || "未填写状态描述"}
                  </p>
                  {!state.deleted_at && (
                    <details className="state-assets">
                      <summary>
                        State reference assets · {state.assets.length}
                        <span className="state-thumbnails">
                          {state.assets.slice(0, 3).map((asset) => (
                            <img
                              key={asset.id}
                              src={assetApi.thumbnail(asset.id)}
                              alt={asset.name}
                              loading="lazy"
                            />
                          ))}
                          {state.assets.length > 3 && (
                            <span>+{state.assets.length - 3}</span>
                          )}
                        </span>
                      </summary>
                      <AssetReferences
                        project={projectId}
                        kind="character-states"
                        id={state.id}
                        assets={state.assets}
                      />
                    </details>
                  )}
                </section>
              ))}
            </div>
          </>
        )}
      </WorkspacePanel>
    </div>
  );
}
