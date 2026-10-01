from pathlib import PurePosixPath

from starlette.concurrency import run_in_threadpool

from app.core.exceptions import AppError
from app.models.assets import Asset, AssetType
from app.repositories.assets import AssetRepository
from app.services.assets import AssetService
from app.services.storage.media import EXTENSIONS

MAX_UPLOAD_SIZE = 512 * 1024 * 1024


class StorageService:
    def __init__(self, workspace):
        self.workspace = workspace

    def storage(self):
        with self.workspace.resources() as (_, storage):
            return storage

    async def upload(
        self, chunks, filename, asset_type=None, *, storyboard=None, create_result=None
    ):
        # Stream directly into this workspace's temp directory, never framework/system temp.
        filename = filename.replace("\\", "/").split("/")[-1].strip()
        if not filename or len(filename) > 255 or any(ord(c) < 32 for c in filename):
            raise AppError("INVALID_FILENAME", "文件名无效。", 422)
        if PurePosixPath(filename).suffix.lower() not in EXTENSIONS:
            raise AppError("UNSUPPORTED_FILE", "支持 PNG、JPEG、WebP、MP4、MOV 和 WebM 文件。", 422)
        storage = await run_in_threadpool(self.storage)
        with storage.stage_upload() as (key, output):
            size = 0
            async for chunk in chunks:
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE:
                    raise AppError("FILE_TOO_LARGE", "单个文件不能超过 512 MiB。", 413)
                await run_in_threadpool(output.write, chunk)
            output.flush()
            output.close()
            if not size:
                raise AppError("EMPTY_FILE", "不能导入空文件。", 422)
            return await run_in_threadpool(
                self.import_staged,
                storage,
                key,
                filename,
                asset_type,
                storyboard=storyboard,
                create_result=create_result,
            )

    def import_staged(
        self, staging, key, filename, asset_type=None, *, storyboard=None, create_result=None
    ):
        with self.workspace.resources() as (database, storage):
            source = staging.get_absolute_path(key)
            if storage.get_absolute_path(key) != source:
                raise AppError("WORKSPACE_CHANGED", "导入期间工作空间已切换，请重新导入。", 409)
            info = storage.inspect_media(key)
            selected = asset_type or (
                AssetType.IMAGE if info.mime_type.startswith("image/") else AssetType.VIDEO
            )
            AssetService.validate_type(selected, info.mime_type)
            stored = None
            thumbnail = None
            try:
                stored = storage.save_file(source, original_filename=filename)
                thumbnail = storage.create_thumbnail(stored.relative_path)
                with database.session() as session:
                    entity = AssetRepository(session).add(
                        Asset(
                            name=filename,
                            asset_type=selected,
                            original_filename=filename,
                            storage_path="storage/" + stored.relative_path,
                            thumbnail_path="storage/" + thumbnail,
                            file_size=stored.file_size,
                            checksum=stored.checksum,
                            mime_type=info.mime_type,
                            width=info.width,
                            height=info.height,
                            duration_seconds=info.duration_seconds,
                        )
                    )
                    if create_result is not None:
                        result = create_result(session, entity.id)
                    elif storyboard is None:
                        result = AssetService(session).detail(entity.id)
                    else:
                        from app.schemas.storyboards import StoryboardCreate
                        from app.services.storyboards import StoryboardService

                        shot_id, source_id, notes = storyboard
                        result = StoryboardService(session).create(
                            shot_id,
                            StoryboardCreate(
                                asset_id=entity.id, source_prompt_record_id=source_id, notes=notes
                            ),
                        )
                return result
            except BaseException:
                if thumbnail:
                    storage.delete_file(thumbnail)
                if stored:
                    storage.delete_file(stored.relative_path)
                raise

    def file(self, identifier, thumbnail=False):
        with self.workspace.resources() as (database, storage):
            with database.session() as session:
                asset = AssetService(session).asset(identifier)
                relative = asset.thumbnail_path if thumbnail else asset.storage_path
                key = relative.removeprefix("storage/")
                if not storage.exists(key):
                    raise AppError("FILE_NOT_FOUND", "资产文件缺失，请检查本地存储。", 404)
                return storage.get_absolute_path(key), (
                    "image/jpeg" if thumbnail else asset.mime_type
                )
