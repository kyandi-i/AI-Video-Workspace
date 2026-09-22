import unicodedata

from app.core.exceptions import AppError
from app.models.assets import AssetTag, AssetType, ProjectAssetLink, ShotAssetLink, Tag
from app.models.base import utc_now
from app.repositories.assets import AssetRepository, TagRepository
from app.repositories.workflow import WorkflowRepository
from app.schemas.assets import AssetDetail, AssetRead, TagRead
from app.schemas.workflow import ProjectRead, ShotRead
from app.services.workflow import WorkflowService, atomic


class AssetService(WorkflowService):
    def __init__(self, session):
        super().__init__(session)
        self.assets = AssetRepository(session)
        self.tags = TagRepository(session)

    def asset(self, identifier, include_deleted=False):
        return self.required(self.assets, identifier, "ASSET", include_deleted)

    def list_tags(self):
        return self.tags.matching()

    def read_many(self, entities):
        tags = {}
        for identifier, tag in self.assets.tags_for([item.id for item in entities]):
            tags.setdefault(identifier, []).append(TagRead.model_validate(tag))
        return [
            AssetRead.model_validate(item).model_copy(update={"tags": tags.get(item.id, [])})
            for item in entities
        ]

    def list_assets(self, **filters):
        if filters.get("project_id"):
            self.project(filters["project_id"])
        if filters.get("shot_id"):
            self.shot(filters["shot_id"])
        return self.read_many(self.assets.search(**filters))

    def detail(self, identifier, include_deleted=False):
        asset = self.read_many([self.asset(identifier, include_deleted)])[0]
        projects, shots = self.assets.references(identifier)
        characters, states = self.assets.character_references(identifier)
        return AssetDetail(
            **asset.model_dump(),
            projects=[ProjectRead.model_validate(item) for item in projects],
            shots=[ShotRead.model_validate(item) for item in shots],
            characters=characters,
            character_states=states,
        )

    @staticmethod
    def validate_type(asset_type, mime):
        if asset_type in {AssetType.IMAGE, AssetType.STORYBOARD_6GRID} and not mime.startswith(
            "image/"
        ):
            raise AppError("INVALID_ASSET_TYPE", "该分类只适用于图片。", 422)
        if asset_type == AssetType.VIDEO and not mime.startswith("video/"):
            raise AppError("INVALID_ASSET_TYPE", "Video 分类只适用于视频。", 422)

    @atomic
    def update_asset(self, identifier, data):
        asset = self.asset(identifier)
        changes = data.model_dump(exclude_unset=True)
        self.validate_type(changes.get("asset_type", asset.asset_type), asset.mime_type)
        self.assets.update(asset, **changes)
        return self.detail(identifier)

    @atomic
    def delete_asset(self, identifier):
        asset = self.asset(identifier)
        projects, shots = self.assets.references(identifier)
        characters, states = self.assets.character_references(identifier)
        if projects or shots or characters or states:
            raise AppError(
                "ASSET_IN_USE",
                "资产仍被项目或镜头引用，或被角色 / 角色状态引用，请先解除绑定再删除。",
                409,
                {
                    "projects": len(projects),
                    "shots": len(shots),
                    "characters": len(characters),
                    "character_states": len(states),
                },
            )
        self.assets.soft_delete(asset)

    @atomic
    def restore_asset(self, identifier):
        self.assets.restore(self.asset(identifier, True))
        return self.detail(identifier)

    @atomic
    def create_tag(self, data):
        name = " ".join(unicodedata.normalize("NFKC", data.name).split())
        if not name or len(name) > 80:
            raise AppError("INVALID_TAG", "标签名称需为 1 至 80 个字符。", 422)
        normalized = name.casefold()
        matches = self.tags.matching(normalized_name=normalized, include_deleted=True)
        return (
            self.tags.restore(matches[0])
            if matches
            else self.tags.add(Tag(name=name, normalized_name=normalized))
        )

    @atomic
    def tag_asset(self, identifier, tag_id, remove=False):
        asset = self.asset(identifier)
        self.required(self.tags, tag_id, "TAG")
        self.link(AssetTag, {"asset_id": identifier, "tag_id": tag_id}, remove)
        self.assets.update(asset, name=asset.name)
        asset.updated_at = utc_now()
        return self.detail(identifier)

    def link(self, model, fields, remove):
        repo = WorkflowRepository(self.session, model)
        existing = repo.matching(include_deleted=True, **fields)
        if existing:
            (repo.soft_delete if remove else repo.restore)(existing[0])
        elif not remove:
            repo.add(model(**fields))

    @atomic
    def bind(self, identifier, owner_id, kind, remove=False):
        self.asset(identifier)
        # Unbind remains possible for a deleted owner; restoration must not trap links.
        (self.project if kind == "project" else self.shot)(owner_id, include_deleted=remove)
        model = ProjectAssetLink if kind == "project" else ShotAssetLink
        self.link(model, {"asset_id": identifier, f"{kind}_id": owner_id}, remove)
        return self.detail(identifier)
