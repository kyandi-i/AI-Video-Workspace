import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Choice } from "@/components/common/entity-form";
import { WorkspacePanel } from "@/components/common/workspace-panel";
import { QueryState, QueryErrors } from "@/components/common/query-state";
import { assetApi } from "@/features/assets/api";
import {
  useCharacters,
  useStates,
  useShotStates,
  useCharacterActions,
} from "./hooks";
import { characterApi } from "./api";
export function ShotCharacters({
  shotId,
  projectId,
}: {
  shotId: string;
  projectId: string;
}) {
  const [character, setCharacter] = useState("");
  const [state, setState] = useState("");
  const [error, setError] = useState("");
  const characters = useCharacters(projectId);
  const states = useStates(projectId, character);
  const linked = useShotStates(shotId);
  const actions = useCharacterActions(projectId);
  async function bind(id: string, remove = false) {
    setError("");
    try {
      await actions.run(() => characterApi.shot(shotId, id, remove));
      setState("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "绑定失败");
    }
  }
  return (
    <WorkspacePanel
      title="Characters"
      description="为此镜头选择每个角色的一个视觉状态。"
    >
      {!linked.data || !characters.data ? (
        <QueryState queries={[linked, characters]} />
      ) : (
        <>
          <QueryErrors queries={[linked, characters]} />
          {!linked.data.length && (
            <p className="muted-copy">尚未绑定角色状态</p>
          )}
          <ul className="shot-character-list">
            {linked.data.map((item) => (
              <li key={item.id}>
                {item.assets[0] && (
                  <img
                    src={assetApi.thumbnail(item.assets[0].id)}
                    alt={item.name}
                    loading="lazy"
                  />
                )}
                <Link
                  to={`/projects/${projectId}/characters/${item.character_id}`}
                  title={`${item.character_name} → ${item.name}`}
                >
                  {item.character_name} → {item.name}
                </Link>
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={actions.isPending}
                  onClick={() => void bind(item.id, true)}
                >
                  解除角色状态绑定
                </Button>
              </li>
            ))}
          </ul>
          {characters.data.length ? (
            <div className="shot-character-picker">
              <Choice
                label="选择角色"
                value={character}
                onChange={(value) => {
                  setCharacter(value);
                  setState("");
                }}
                disabled={actions.isPending}
                options={characters.data.map((c) => ({
                  value: c.id,
                  label: c.name,
                }))}
              />
              {character &&
                (!states.data ? (
                  <QueryState queries={[states]} />
                ) : (
                  <>
                    <QueryErrors queries={[states]} />
                    <Choice
                      label="选择角色状态"
                      value={state}
                      onChange={setState}
                      disabled={actions.isPending || !states.data.length}
                      options={states.data.map((s) => ({
                        value: s.id,
                        label: s.name,
                      }))}
                    />
                    {!states.data.length && <p>该角色尚无状态</p>}
                  </>
                ))}
              <Button
                disabled={!state || actions.isPending}
                onClick={() => void bind(state)}
              >
                Add Character State
              </Button>
            </div>
          ) : (
            <Link
              className="back-link"
              to={`/projects/${projectId}/characters`}
            >
              创建项目角色 →
            </Link>
          )}
          {error && (
            <p className="error-banner" role="alert">
              {error}
            </p>
          )}
        </>
      )}
    </WorkspacePanel>
  );
}
