import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Users } from "lucide-react";
import { requestJson } from "@/api/client";
import { WorkspacePanel } from "@/components/common/workspace-panel";
import { Choice } from "@/components/common/entity-form";
import { QueryState, QueryErrors } from "@/components/common/query-state";
import { Button } from "@/components/ui/button";
import { assetApi } from "@/features/assets/api";
import { useCharacters, useStates } from "@/features/characters/hooks";
import { characterApi } from "@/features/characters/api";
import type { ShotState } from "@/features/characters/types";

export function WorkspaceCharacters({
  shotId,
  projectId,
  linked,
}: {
  shotId: string;
  projectId: string;
  linked: ShotState[];
}) {
  const [character, setCharacter] = useState("");
  const [state, setState] = useState("");
  const characters = useCharacters(projectId);
  const states = useStates(projectId, character);
  const client = useQueryClient();
  const mutation = useMutation({
    mutationFn: ({ id, remove }: { id: string; remove?: boolean }) =>
      remove
        ? characterApi.shot(shotId, id, true)
        : requestJson(`/shots/${shotId}/character-states`, "PUT", {
            character_state_id: id,
          }),
    onSuccess: async () => {
      setState("");
      await Promise.all([
        client.invalidateQueries({ queryKey: ["shot-workspace", shotId] }),
        client.invalidateQueries({ queryKey: ["shot-characters", shotId] }),
        client.invalidateQueries({ queryKey: ["characters", projectId] }),
      ]);
    },
  });
  const replacing = linked.some((item) => item.character_id === character);
  return (
    <WorkspacePanel
      title="Characters"
      description="角色身份与当前视觉状态 · 修改即时保存"
    >
      {!linked.length && <p className="muted-copy">No characters assigned</p>}
      {linked.map((item) => {
        const cover =
          item.assets.find((a) => a.asset_type === "IMAGE") ??
          item.character_assets.find((a) => a.asset_type === "IMAGE");
        return (
          <article className="workspace-character" key={item.id}>
            <div className="workspace-character-heading">
              {cover ? (
                <img
                  src={assetApi.thumbnail(cover.id)}
                  alt={item.name}
                  loading="lazy"
                />
              ) : (
                <Users aria-label="No reference image" />
              )}
              <div>
                <Link
                  className="back-link"
                  to={`/projects/${projectId}/characters/${item.character_id}`}
                >
                  {item.character_name}
                </Link>
                <strong>{item.name}</strong>
              </div>
            </div>
            {item.character_description && <p>{item.character_description}</p>}
            {item.character_notes && <p>{item.character_notes}</p>}
            {item.description && <p>{item.description}</p>}
            {[
              { label: "Character references", assets: item.character_assets },
              { label: "State references", assets: item.assets },
            ].map(
              ({ label, assets }) =>
                assets.length > 0 && (
                  <div key={label}>
                    <span className="muted-copy">{label}</span>
                    <div className="workspace-thumbnails">
                      {assets.slice(0, 3).map((a) => (
                        <img
                          key={a.id}
                          src={assetApi.thumbnail(a.id)}
                          alt={a.name}
                          title={a.name}
                          loading="lazy"
                        />
                      ))}
                      {assets.length > 3 && <span>+{assets.length - 3}</span>}
                    </div>
                  </div>
                ),
            )}
            <div className="row-actions">
              <Button
                size="sm"
                variant="secondary"
                disabled={mutation.isPending}
                onClick={() => {
                  setCharacter(item.character_id);
                  setState(item.id);
                }}
              >
                Change State
              </Button>
              <Button
                size="sm"
                variant="ghost"
                disabled={mutation.isPending}
                onClick={() => mutation.mutate({ id: item.id, remove: true })}
              >
                Remove
              </Button>
            </div>
          </article>
        );
      })}
      {!characters.data ? (
        <QueryState queries={[characters]} />
      ) : (
        <div className="workspace-state-picker">
          <QueryErrors queries={[characters]} />
          <Choice
            label="选择角色"
            value={character}
            onChange={(v) => {
              setCharacter(v);
              setState("");
            }}
            options={characters.data.map((c) => ({
              value: c.id,
              label: c.name,
            }))}
            disabled={mutation.isPending}
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
                  options={states.data.map((s) => ({
                    value: s.id,
                    label: s.name,
                  }))}
                  disabled={mutation.isPending || !states.data.length}
                />
              </>
            ))}
          <Button
            disabled={!state || mutation.isPending}
            onClick={() => mutation.mutate({ id: state })}
          >
            {replacing ? "Replace State" : "Add Character State"}
          </Button>
          {!characters.data.length && (
            <Link
              className="back-link"
              to={`/projects/${projectId}/characters`}
            >
              创建项目角色 →
            </Link>
          )}
        </div>
      )}
      {mutation.error && (
        <p className="error-banner" role="alert">
          {mutation.error.message}
        </p>
      )}
    </WorkspacePanel>
  );
}
