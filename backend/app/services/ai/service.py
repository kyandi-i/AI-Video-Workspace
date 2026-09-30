import hashlib
import json

from app.core.exceptions import AppError
from app.models.prompts import PromptRecord
from app.repositories.prompts import PromptRepository
from app.schemas.ai import PromptGenerate, PromptPreview
from app.services.ai.context import build_shot_context
from app.services.ai.provider import AIProvider
from app.services.ai.settings import AISettingsService
from app.services.template_placeholders import render_content
from app.services.templates import PromptTemplateService
from app.services.workflow import ShotService


class AIService:
    def __init__(self, session, provider: AIProvider, settings: AISettingsService):
        self.session, self.provider, self.settings = session, provider, settings
        self.records = PromptRepository(session)

    def prepare(self, shot_id, template_id):
        shot, context = build_shot_context(self.session, shot_id)
        template = PromptTemplateService(self.session).detail(template_id)
        if template.project_id and template.project_id != shot.project_id:
            raise AppError("TEMPLATE_PROJECT_MISMATCH", "模板不属于当前镜头项目。", 400)
        rendered = render_content(template.template_content, context)
        if not rendered.strip():
            raise AppError("AI_EMPTY_INPUT", "模板渲染结果为空，请完善镜头要求。", 400)
        if len(rendered) > 200_000:
            raise AppError("AI_INPUT_TOO_LARGE", "渲染输入过长，请精简模板或上下文。", 400)
        digest = hashlib.sha256(
            json.dumps(
                [str(shot_id), str(template.id), template.template_content, context, rendered],
                ensure_ascii=False,
                sort_keys=True,
            ).encode()
        ).hexdigest()
        return template, PromptPreview(
            template_id=template.id,
            template_name=template.name,
            rendered_input=rendered,
            context=context,
            input_hash=digest,
        )

    def preview(self, shot_id, template_id):
        return self.prepare(shot_id, template_id)[1]

    def latest(self, shot_id):
        ShotService(self.session).shot(shot_id)
        return self.records.latest(shot_id)

    def detail(self, identifier):
        record = self.records.get(identifier)
        if record is None:
            raise AppError("PROMPT_NOT_FOUND", "生成记录不存在。", 404)
        ShotService(self.session).shot(record.shot_id)
        return record

    def history(self, shot_id, prompt_type=None):
        ShotService(self.session).shot(shot_id)
        return self.records.history(shot_id, prompt_type)

    def edit(self, identifier, data):
        return self.records.update(self.detail(identifier), edited_content=data.edited_content)

    def select(self, identifier):
        record = self.detail(identifier)
        self.records.clear_selection(record.shot_id, record.prompt_type)
        return self.records.update(record, is_selected=True)

    def regenerate(self, identifier, data):
        source = self.detail(identifier)
        if data.operation_id == source.id:
            raise AppError("AI_OPERATION_CONFLICT", "重新生成必须使用新的操作标识。", 409)
        template = PromptTemplateService(self.session).detail(source.template_id)
        if template.category.value != source.prompt_type:
            raise AppError(
                "PROMPT_TYPE_CHANGED", "来源模板类型已变更，请选择模板重新 Generate。", 409
            )
        return self.generate(
            source.shot_id,
            PromptGenerate(
                template_id=source.template_id,
                operation_id=data.operation_id,
                input_hash=data.input_hash,
            ),
        )

    def generate(self, shot_id, data):
        ShotService(self.session).shot(shot_id)
        existing = self.records.get(data.operation_id)
        if existing:
            if (
                existing.shot_id != shot_id
                or existing.template_id != data.template_id
                or existing.input_hash != data.input_hash
            ):
                raise AppError("AI_OPERATION_CONFLICT", "生成操作标识已被其他输入使用。", 409)
            return existing
        template, preview = self.prepare(shot_id, data.template_id)
        if preview.input_hash != data.input_hash:
            raise AppError("AI_INPUT_CHANGED", "上下文或模板已变化，请刷新输入预览。", 409)
        config = self.settings.configured()
        snapshot_text = json.dumps(
            [preview.rendered_input, preview.context, template.template_content], ensure_ascii=False
        )
        if config.api_key.get_secret_value() in snapshot_text:
            raise AppError("AI_SENSITIVE_INPUT", "输入包含当前 API Key，请移除后重试。", 400)
        try:
            content = self.provider.generate(preview.rendered_input, config, str(data.operation_id))
        except AppError as exc:
            safe_errors = {
                "AI_AUTH_ERROR": ("Provider 拒绝认证，请检查 API Key。", 502),
                "AI_MODEL_ERROR": ("请检查模型名称与 API Base URL。", 502),
                "AI_TIMEOUT": ("AI 请求超时，请稍后重试。", 504),
                "AI_CONNECTION_ERROR": ("无法连接 AI Provider。", 502),
                "AI_INVALID_RESPONSE": ("AI Provider 返回格式无效。", 502),
            }
            code = exc.code if exc.code in safe_errors else "AI_PROVIDER_ERROR"
            message, status = safe_errors.get(code, ("AI Provider 请求失败，请重试。", 502))
            raise AppError(code, message, status) from None
        except TimeoutError:
            raise AppError("AI_TIMEOUT", "AI 请求超时，请稍后重试。", 504) from None
        except Exception:
            # Provider exceptions must not reach the generic traceback logger.
            raise AppError(
                "AI_PROVIDER_ERROR", "AI Provider 请求失败，请检查设置后重试。", 502
            ) from None
        if not isinstance(content, str):
            raise AppError("AI_INVALID_RESPONSE", "AI Provider 返回格式无效。", 502)
        if not content.strip():
            raise AppError("AI_EMPTY_RESPONSE", "AI Provider 未返回内容，请重试。", 502)
        if len(content) > 500_000:
            raise AppError("AI_INVALID_RESPONSE", "AI Provider 返回内容过长。", 502)
        # Do not persist an accidentally echoed credential in ordinary project data.
        if config.api_key.get_secret_value() in content:
            raise AppError("AI_INVALID_RESPONSE", "AI Provider 返回内容不可安全保存。", 502)
        # The request's Workspace lease and transaction cover allocation, insert and
        # selection. This write acquires SQLite's writer lock before reading MAX;
        # cross-process stale read transactions fail/rollback instead of duplicating.
        self.records.clear_selection(shot_id, template.category.value)
        version = self.records.max_version(shot_id, template.category.value) + 1
        return self.records.add(
            PromptRecord(
                id=data.operation_id,
                shot_id=shot_id,
                template_id=template.id,
                template_name=template.name,
                template_content=template.template_content,
                prompt_type=template.category.value,
                context_json=preview.context,
                rendered_input=preview.rendered_input,
                input_hash=preview.input_hash,
                generated_content=content,
                provider=self.provider.name,
                model_name=config.model,
                version=version,
                is_selected=True,
            )
        )
