from __future__ import annotations

import asyncio
import json

import httpx

from apps.api.app.providers import OpenAICompatibleProvider


def test_openai_compatible_provider_contract() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://model.example/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer private-test-key"
        payload = json.loads(request.content)
        assert payload["model"] == "example-model"
        assert payload["messages"][0]["role"] == "user"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"product_title":"测试返回"}'
                        }
                    }
                ]
            },
        )

    provider = OpenAICompatibleProvider(
        base_url="https://model.example/v1",
        api_key="private-test-key",
        model="example-model",
        transport=httpx.MockTransport(handler),
    )
    content = asyncio.run(
        provider.generate([{"role": "user", "content": "生成测试内容"}])
    )
    assert content == '{"product_title":"测试返回"}'
