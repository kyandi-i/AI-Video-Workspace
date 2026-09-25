import json
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from app.core.exceptions import AppError
from app.schemas.ai import ProviderUpdate


class AIProvider(Protocol):
    name: str

    def generate(self, rendered_input: str, config: ProviderUpdate, operation_id: str) -> str: ...


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward the Authorization header to another endpoint.
        return None


class OpenAICompatibleProvider:
    name = "openai-compatible"
    timeout = 45
    response_limit = 1_000_000

    def __init__(self, opener=None):
        self.opener = opener or build_opener(NoRedirect())

    def generate(self, rendered_input, config, operation_id):
        request = Request(
            config.api_base_url + "/chat/completions",
            data=json.dumps(
                {
                    "model": config.model,
                    "messages": [{"role": "user", "content": rendered_input}],
                    "stream": False,
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + config.api_key.get_secret_value(),
                "Idempotency-Key": operation_id,
            },
            method="POST",
        )
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                raw = response.read(self.response_limit + 1)
            if len(raw) > self.response_limit:
                raise ValueError()
            body = json.loads(raw)
            content = body["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise ValueError()
            return content
        except HTTPError as exc:
            status = exc.code
            exc.close()
            if status in (401, 403):
                raise AppError(
                    "AI_AUTH_ERROR", "Provider 拒绝认证，请检查 API Key。", 502
                ) from None
            if status in (400, 404, 422):
                raise AppError("AI_MODEL_ERROR", "请检查模型名称与 API Base URL。", 502) from None
            raise AppError("AI_PROVIDER_ERROR", "AI Provider 暂时无法完成请求。", 502) from None
        except TimeoutError:
            raise AppError("AI_TIMEOUT", "AI 请求超时，请稍后重试。", 504) from None
        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise AppError("AI_TIMEOUT", "AI 请求超时，请稍后重试。", 504) from None
            raise AppError("AI_CONNECTION_ERROR", "无法连接 AI Provider。", 502) from None
        except (OSError, ConnectionError):
            raise AppError("AI_CONNECTION_ERROR", "无法连接 AI Provider。", 502) from None
        except (ValueError, TypeError, KeyError, IndexError):
            raise AppError("AI_INVALID_RESPONSE", "AI Provider 返回格式无效。", 502) from None
