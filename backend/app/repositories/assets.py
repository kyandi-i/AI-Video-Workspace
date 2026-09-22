from sqlalchemy import select

from app.models.assets import Asset, AssetTag, ProjectAssetLink, ShotAssetLink, Tag
from app.models.characters import (
    Character,
    CharacterAssetLink,
    CharacterState,
    CharacterStateAssetLink,
)
from app.models.workflow import Project, Shot
from app.repositories.workflow import WorkflowRepository


class AssetRepository(WorkflowRepository):
    def character_references(self, identifier):
        return tuple(
            list(
                self.session.scalars(
                    select(owner)
                    .join(link)
                    .where(link.asset_id == identifier, link.deleted_at.is_(None))
                )
            )
            for owner, link in (
                (Character, CharacterAssetLink),
                (CharacterState, CharacterStateAssetLink),
            )
        )

    def __init__(self, session):
        super().__init__(session, Asset)

    def search(
        self,
        *,
        search=None,
        asset_type=None,
        tag_id=None,
        project_id=None,
        shot_id=None,
        include_deleted=False,
        offset=0,
        limit=100,
    ):
        query = select(Asset)
        if not include_deleted:
            query = query.where(Asset.deleted_at.is_(None))
        if search:
            query = query.where(
                Asset.name.icontains(search, autoescape=True)
                | Asset.original_filename.icontains(search, autoescape=True)
            )
        if asset_type:
            query = query.where(Asset.asset_type == asset_type)
        for model, field, value in (
            (AssetTag, AssetTag.tag_id, tag_id),
            (ProjectAssetLink, ProjectAssetLink.project_id, project_id),
            (ShotAssetLink, ShotAssetLink.shot_id, shot_id),
        ):
            if value:
                query = query.where(
                    select(model.id)
                    .where(model.asset_id == Asset.id, field == value, model.deleted_at.is_(None))
                    .exists()
                )
        return list(
            self.session.scalars(
                query.order_by(Asset.created_at.desc(), Asset.id).offset(offset).limit(limit)
            )
        )

    def tags_for(self, asset_ids):
        return self.session.execute(
            select(AssetTag.asset_id, Tag)
            .join(Tag)
            .where(
                AssetTag.asset_id.in_(asset_ids),
                AssetTag.deleted_at.is_(None),
                Tag.deleted_at.is_(None),
            )
            .order_by(Tag.name)
        ).all()

    def references(self, identifier):
        # Retain references to soft-deleted owners so later restore remains safe.
        projects = list(
            self.session.scalars(
                select(Project)
                .join(ProjectAssetLink)
                .where(
                    ProjectAssetLink.asset_id == identifier, ProjectAssetLink.deleted_at.is_(None)
                )
            )
        )
        shots = list(
            self.session.scalars(
                select(Shot)
                .join(ShotAssetLink)
                .where(ShotAssetLink.asset_id == identifier, ShotAssetLink.deleted_at.is_(None))
            )
        )
        return projects, shots


class TagRepository(WorkflowRepository):
    def __init__(self, session):
        super().__init__(session, Tag)
