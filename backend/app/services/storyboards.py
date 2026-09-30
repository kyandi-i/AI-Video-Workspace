from app.core.exceptions import AppError
from app.models.assets import AssetType, ProjectAssetLink, ShotAssetLink
from app.models.storyboards import Storyboard
from app.repositories.prompts import PromptRepository
from app.repositories.storyboards import StoryboardRepository
from app.schemas.storyboards import StoryboardRead, StoryboardSource
from app.services.assets import AssetService
from app.services.workflow import WorkflowService, atomic


class StoryboardService(WorkflowService):
    def __init__(self, session):
        super().__init__(session)
        self.records = StoryboardRepository(session)
        self.prompts = PromptRepository(session)
        self.asset_service = AssetService(session)

    def source(self, shot_id, identifier):
        if identifier is None:
            return None
        record = self.required(self.prompts, identifier, "PROMPT")
        if record.shot_id != shot_id:
            raise AppError("STORYBOARD_PROMPT_MISMATCH", "来源 Prompt 必须属于当前镜头。", 400)
        return record

    def read(self, record):
        prompt = self.source(record.shot_id, record.source_prompt_record_id)
        # The media fact is asset_id; a Reference Asset link is never required here.
        asset = self.asset_service.asset(record.asset_id, include_deleted=True)
        return StoryboardRead(
            **{c.name: getattr(record, c.name) for c in Storyboard.__table__.columns},
            asset=self.asset_service.read_many([asset])[0],
            source_prompt=StoryboardSource(
                id=prompt.id,
                version=prompt.version,
                prompt_type=prompt.prompt_type,
                is_edited=prompt.edited_content is not None,
            )
            if prompt
            else None,
        )

    def detail(self, identifier, include_deleted=False):
        record = self.required(self.records, identifier, "STORYBOARD", include_deleted)
        self.shot(record.shot_id, include_deleted)
        return self.read(record)

    def history(self, shot_id, include_deleted=False):
        self.shot(shot_id, include_deleted)
        return [self.read(r) for r in self.records.history(shot_id, include_deleted)]

    @atomic
    def create(self, shot_id, data):
        shot = self.shot(shot_id)
        self.source(shot_id, data.source_prompt_record_id)
        asset = self.asset_service.asset(data.asset_id)
        if asset.asset_type != AssetType.STORYBOARD_6GRID:
            raise AppError(
                "INVALID_STORYBOARD_ASSET", "分镜必须使用 Storyboard 6-Grid 图片资产。", 422
            )
        self.records.clear_selection(shot_id)
        version = self.records.max_version(shot_id) + 1
        # Convenience transaction only: these links have independent lifecycles.
        self.asset_service.link(
            ProjectAssetLink, {"project_id": shot.project_id, "asset_id": asset.id}, False
        )
        self.asset_service.link(ShotAssetLink, {"shot_id": shot_id, "asset_id": asset.id}, False)
        record = self.records.add(
            Storyboard(shot_id=shot_id, version=version, is_selected=True, **data.model_dump())
        )
        return self.read(record)

    @atomic
    def select(self, identifier):
        record = self.required(self.records, identifier, "STORYBOARD")
        self.shot(record.shot_id)
        self.records.clear_selection(record.shot_id)
        self.records.update(record, is_selected=True)
        return self.read(record)

    @atomic
    def delete(self, identifier):
        record = self.required(self.records, identifier, "STORYBOARD")
        # Allow releasing a reference even when its Shot or Project is deleted.
        self.shot(record.shot_id, include_deleted=True)
        self.records.soft_delete(record)

    @atomic
    def restore(self, identifier):
        record = self.required(self.records, identifier, "STORYBOARD", True)
        self.shot(record.shot_id)
        if record.deleted_at is not None:
            asset = self.asset_service.asset(record.asset_id)
            if asset.asset_type != AssetType.STORYBOARD_6GRID:
                raise AppError("INVALID_STORYBOARD_ASSET", "请先恢复六宫格资产及分类。", 422)
            self.source(record.shot_id, record.source_prompt_record_id)
            # Restoration neither selects nor recreates independent links.
            record.is_selected = False
            self.records.restore(record)
        return self.read(record)
