from sqlalchemy.exc import IntegrityError

from app.core.exceptions import AppError
from app.models.characters import (
    Character,
    CharacterAssetLink,
    CharacterState,
    CharacterStateAssetLink,
    ShotCharacterStateLink,
)
from app.repositories.characters import (
    CharacterLinkRepository,
    CharacterRepository,
    CharacterStateRepository,
)
from app.repositories.workflow import WorkflowRepository
from app.schemas.characters import CharacterRead, ShotStateRead, StateRead
from app.services.assets import AssetService
from app.services.character_lifecycle import CharacterLifecycle
from app.services.workflow import WorkflowService, atomic


class CharacterService(WorkflowService):
    def __init__(self, session):
        super().__init__(session)
        self.characters = CharacterRepository(session)
        self.states = CharacterStateRepository(session)
        self.shot_links = WorkflowRepository(session, ShotCharacterStateLink)
        self.lifecycle = CharacterLifecycle(session)
        self.asset_service = AssetService(session)

    def character(self, identifier, include_deleted=False):
        entity = self.required(self.characters, identifier, "CHARACTER", include_deleted)
        self.project(entity.project_id, include_deleted)
        return entity

    def state(self, identifier, include_deleted=False):
        entity = self.required(self.states, identifier, "CHARACTER_STATE", include_deleted)
        self.character(entity.character_id, include_deleted)
        return entity

    def assets_for(self, identifier, state=False):
        model = CharacterStateAssetLink if state else CharacterAssetLink
        field = "character_state_id" if state else "character_id"
        return self.asset_service.read_many(
            CharacterLinkRepository(self.session, model).assets(**{field: identifier})
        )

    def read_character(self, entity):
        assets = self.assets_for(entity.id)
        return CharacterRead.model_validate(entity).model_copy(
            update={
                "assets": assets,
                "asset_count": len(assets),
                "state_count": self.states.count(character_id=entity.id),
            }
        )

    def read_state(self, entity):
        return StateRead.model_validate(entity).model_copy(
            update={
                "assets": self.assets_for(entity.id, True),
                "shot_usage_count": self.shot_links.count(character_state_id=entity.id),
            }
        )

    def list_characters(self, project_id, search=None, include_deleted=False):
        self.project(project_id, include_deleted)
        return [
            self.read_character(e)
            for e in self.characters.search(project_id, search, include_deleted)
        ]

    def list_states(self, character_id, include_deleted=False):
        self.character(character_id, include_deleted)
        return [
            self.read_state(e)
            for e in self.states.matching(
                character_id=character_id, include_deleted=include_deleted
            )
        ]

    def save_named(self, repo, model, parent, data, entity=None, **extra):
        name = data.get("name", entity.name if entity else "")
        code = (
            "CHARACTER_STATE_NAME_CONFLICT"
            if model is CharacterState
            else "CHARACTER_NAME_CONFLICT"
        )
        matches = repo.matching(**parent, name=name, include_deleted=True)
        if any(e.id != (entity.id if entity else None) for e in matches):
            raise AppError(
                code, "该名称已存在（包含已删除记录），请使用其他名称或恢复原记录。", 409
            )
        try:
            return (
                repo.update(entity, **data)
                if entity
                else repo.add(model(**parent, **data, **extra))
            )
        except IntegrityError as exc:
            raise AppError(code, "该名称已存在，请使用其他名称。", 409) from exc

    @atomic
    def create_character(self, project_id, data):
        self.project(project_id)
        return self.read_character(
            self.save_named(
                self.characters, Character, {"project_id": project_id}, data.model_dump()
            )
        )

    @atomic
    def update_character(self, identifier, data):
        entity = self.character(identifier)
        return self.read_character(
            self.save_named(
                self.characters,
                Character,
                {"project_id": entity.project_id},
                data.model_dump(exclude_unset=True),
                entity,
            )
        )

    @atomic
    def delete_character(self, identifier):
        self.lifecycle.delete_character(self.character(identifier), self.deletion_timestamp())

    @atomic
    def restore_character(self, identifier):
        entity = self.character(identifier, True)
        self.project(entity.project_id)
        self.lifecycle.restore_character(entity)
        return self.read_character(entity)

    @atomic
    def create_state(self, character_id, data):
        self.character(character_id)
        return self.read_state(
            self.save_named(
                self.states,
                CharacterState,
                {"character_id": character_id},
                data.model_dump(),
                order_index=len(self.states.matching(character_id=character_id)),
            )
        )

    @atomic
    def update_state(self, identifier, data):
        entity = self.state(identifier)
        return self.read_state(
            self.save_named(
                self.states,
                CharacterState,
                {"character_id": entity.character_id},
                data.model_dump(exclude_unset=True),
                entity,
            )
        )

    @atomic
    def delete_state(self, identifier):
        entity = self.state(identifier)
        count = self.shot_links.count(character_state_id=identifier)
        if count:
            raise AppError(
                "CHARACTER_STATE_IN_USE",
                f"该角色状态正在被 {count} 个镜头使用。请先解除镜头绑定。",
                409,
                {"shots": count},
            )
        self.lifecycle.delete_state(entity, self.deletion_timestamp())
        self.lifecycle.normalize(entity.character_id)

    @atomic
    def restore_state(self, identifier):
        entity = self.state(identifier, True)
        self.character(entity.character_id)
        if entity.deleted_at is not None:
            self.states.update(
                entity, order_index=len(self.states.matching(character_id=entity.character_id))
            )
            self.states.restore(entity)
        return self.read_state(entity)

    @atomic
    def move_state(self, identifier, direction):
        if direction not in {"up", "down"}:
            raise AppError("INVALID_DIRECTION", "移动方向必须为 up 或 down。", 422)
        entity = self.state(identifier)
        siblings = self.states.matching(character_id=entity.character_id)
        index = siblings.index(entity)
        target = index + (-1 if direction == "up" else 1)
        if 0 <= target < len(siblings):
            siblings[index], siblings[target] = siblings[target], siblings[index]
        for order, sibling in enumerate(siblings):
            self.states.update(sibling, order_index=order)
        return [self.read_state(e) for e in siblings]

    @atomic
    def bind_asset(self, identifier, asset_id, state=False, remove=False):
        entity = (self.state if state else self.character)(identifier, remove)
        self.asset_service.asset(asset_id, remove)
        model = CharacterStateAssetLink if state else CharacterAssetLink
        field = "character_state_id" if state else "character_id"
        self.asset_service.link(model, {field: identifier, "asset_id": asset_id}, remove)
        return (self.read_state if state else self.read_character)(entity)

    def list_shot_states(self, shot_id):
        self.shot(shot_id)
        result = []
        for link in self.shot_links.matching(shot_id=shot_id):
            state = self.state(link.character_state_id)
            result.append(
                ShotStateRead(
                    **self.read_state(state).model_dump(),
                    character_name=self.character(state.character_id).name,
                )
            )
        return result

    @atomic
    def bind_shot(self, shot_id, state_id, remove=False):
        shot = self.shot(shot_id, remove)
        state = self.state(state_id, remove)
        character = self.character(state.character_id, remove)
        if shot.project_id != character.project_id:
            raise AppError("INVALID_PROJECT_RELATION", "角色状态与镜头必须属于同一项目。", 400)
        if not remove:
            existing = self.shot_links.matching(shot_id=shot_id, character_id=character.id)
            if any(link.character_state_id != state_id for link in existing):
                raise AppError(
                    "SHOT_CHARACTER_STATE_CONFLICT",
                    "该镜头已绑定此角色的其他状态，请先解除原绑定。",
                    409,
                )
        try:
            self.asset_service.link(
                ShotCharacterStateLink,
                {
                    "shot_id": shot_id,
                    "character_state_id": state_id,
                    "character_id": character.id,
                },
                remove,
            )
        except IntegrityError as exc:
            raise AppError(
                "SHOT_CHARACTER_STATE_CONFLICT", "该镜头已绑定此角色的其他状态。", 409
            ) from exc
        return self.list_shot_states(shot_id) if shot.deleted_at is None else []
