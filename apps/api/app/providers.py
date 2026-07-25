from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from .settings import Settings


class ProviderConfigError(RuntimeError):
    """The configured provider is incomplete or unsupported."""


class ProviderCallError(RuntimeError):
    """The configured model request failed."""


@dataclass(slots=True)
class OpenAICompatibleProvider:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float = 90
    transport: httpx.AsyncBaseTransport | None = None

    async def generate(self, messages: list[dict[str, str]]) -> str:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.4,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise ProviderCallError(
                f"无法连接模型服务：{type(exc).__name__}"
            ) from exc

        if response.status_code >= 400:
            raise ProviderCallError(
                f"模型服务返回 HTTP {response.status_code}"
            )
        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderCallError("模型服务返回了无法识别的响应结构") from exc
        if not isinstance(content, str) or not content.strip():
            raise ProviderCallError("模型服务没有返回文本内容")
        return content.strip()


def configured_provider(settings: Settings) -> OpenAICompatibleProvider:
    if settings.provider != "openai-compatible":
        raise ProviderConfigError(
            "尚未配置真实模型。请在 .env 中设置 "
            "AICOWORK_PROVIDER=openai-compatible。"
        )
    missing: list[str] = []
    if not settings.base_url:
        missing.append("AICOWORK_BASE_URL")
    if not settings.api_key:
        missing.append("AICOWORK_API_KEY")
    if not settings.model:
        missing.append("AICOWORK_MODEL")
    if missing:
        raise ProviderConfigError(f"缺少模型配置：{', '.join(missing)}")
    return OpenAICompatibleProvider(
        base_url=settings.base_url,
        api_key=settings.api_key,
        model=settings.model,
    )
