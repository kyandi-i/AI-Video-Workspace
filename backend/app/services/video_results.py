from app.core.exceptions import AppError
from app.models.assets import AssetType, ProjectAssetLink, ShotAssetLink
from app.models.video_results import VideoResult
from app.repositories.prompts import PromptRepository
from app.repositories.storyboards import StoryboardRepository
from app.repositories.video_results import VideoResultRepository
from app.schemas.storyboards import StoryboardSource
from app.schemas.video_results import VideoResultRead, VideoStoryboardSource
from app.services.assets import AssetService
from app.services.workflow import WorkflowService, atomic


class VideoResultService(WorkflowService):
    def __init__(self, session):
        super().__init__(session)
        self.records = VideoResultRepository(session)
        self.asset_service = AssetService(session)

    def sources(self, shot_id, storyboard_id, prompt_id, historical=False):
        result = []
        for repo, identifier, code in (
            (StoryboardRepository(self.session), storyboard_id, "STORYBOARD"),
            (PromptRepository(self.session), prompt_id, "PROMPT"),
        ):
            record = self.required(repo, identifier, code, historical) if identifier else None
            if record and record.shot_id != shot_id:
                raise AppError("VIDEO_RESULT_SOURCE_MISMATCH", "视频来源必须属于当前镜头。", 400)
            result.append(record)
        return result

    def read(self, record):
        storyboard, prompt = self.sources(
            record.shot_id,
            record.source_storyboard_id,
            record.source_prompt_record_id,
            historical=True,
        )
        asset = self.asset_service.asset(record.asset_id, include_deleted=True)
        return VideoResultRead(
            **{c.name: getattr(record, c.name) for c in VideoResult.__table__.columns},
            asset=self.asset_service.read_many([asset])[0],
            source_storyboard=VideoStoryboardSource(
                id=storyboard.id,
                version=storyboard.version,
                is_deleted=storyboard.deleted_at is not None,
            )
            if storyboard
            else None,
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
        record = self.required(self.records, identifier, "VIDEO_RESULT", include_deleted)
        self.shot(record.shot_id, include_deleted)
        return self.read(record)

    def history(self, shot_id, include_deleted=False):
        self.shot(shot_id, include_deleted)
        return [self.read(r) for r in self.records.history(shot_id, include_deleted)]

    def validate_asset(self, identifier):
        asset = self.asset_service.asset(identifier)
        if asset.asset_type != AssetType.VIDEO:
            raise AppError("INVALID_VIDEO_RESULT_ASSET", "视频结果必须使用 Video 资产。", 422)
        return asset

    @atomic
    def create(self, shot_id, data):
        shot = self.shot(shot_id)
        self.sources(shot_id, data.source_storyboard_id, data.source_prompt_record_id)
        asset = self.validate_asset(data.asset_id)
        self.records.clear_selection(shot_id)
        version = self.records.max_version(shot_id) + 1
        self.asset_service.link(
            ProjectAssetLink, {"project_id": shot.project_id, "asset_id": asset.id}, False
        )
        self.asset_service.link(ShotAssetLink, {"shot_id": shot_id, "asset_id": asset.id}, False)
        return self.read(
            self.records.add(
                VideoResult(shot_id=shot_id, version=version, is_selected=True, **data.model_dump())
            )
        )

    @atomic
    def select(self, identifier):
        record = self.required(self.records, identifier, "VIDEO_RESULT")
        self.shot(record.shot_id)
        self.records.clear_selection(record.shot_id)
        self.records.update(record, is_selected=True)
        return self.read(record)

    @atomic
    def delete(self, identifier):
        record = self.required(self.records, identifier, "VIDEO_RESULT")
        self.shot(record.shot_id, include_deleted=True)
        self.records.soft_delete(record)

    @atomic
    def restore(self, identifier):
        record = self.required(self.records, identifier, "VIDEO_RESULT", True)
        self.shot(record.shot_id)
        if record.deleted_at is not None:
            self.validate_asset(record.asset_id)
            self.sources(
                record.shot_id,
                record.source_storyboard_id,
                record.source_prompt_record_id,
                historical=True,
            )
            record.is_selected = False
            self.records.restore(record)
        return self.read(record)
