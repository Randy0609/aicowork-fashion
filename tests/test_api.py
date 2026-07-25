from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.app import main as main_module
from apps.api.app.main import create_app
from apps.api.app.settings import Settings


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_public_metadata_and_demo_workflow(tmp_path: Path) -> None:
    settings = Settings(
        root_dir=ROOT_DIR,
        data_dir=tmp_path / "runtime",
        web_dist=tmp_path / "missing-web-dist",
    )
    with TestClient(create_app(settings)) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        workflows = client.get("/api/workflows")
        assert workflows.status_code == 200
        assert [item["id"] for item in workflows.json()["items"]] == [
            "product-content"
        ]
        assert "handler" not in workflows.text

        categories = client.get("/api/categories")
        assert categories.status_code == 200
        assert {item["id"] for item in categories.json()["items"]} == {
            "apparel",
            "eyewear",
            "shoes-bags",
        }

        response = client.post(
            "/api/workflows/product-content/run",
            json={
                "provider": "demo",
                "inputs": {
                    "category": "女装上衣",
                    "product_name": "测试针织衫",
                    "material": "棉混纺，比例待核实",
                    "target_customer": "日常通勤人群",
                    "selling_points": "圆领版型；袖口罗纹；颜色以实物为准",
                    "tone": "克制专业",
                },
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["task"]["status"] == "completed"
        assert body["task"]["provider"] == "demo"
        assert body["artifact"]["content"]["generation_mode"] == "demo"
        assert body["artifact"]["content"]["product_title"] == "测试针织衫｜女装上衣"
        assert "关注关注" not in body["artifact"]["content"]["social_post"]

        artifacts = client.get("/api/artifacts")
        assert artifacts.status_code == 200
        assert len(artifacts.json()["items"]) == 1

        artifact_id = body["artifact"]["id"]
        persisted = client.get(f"/api/artifacts/{artifact_id}")
        assert persisted.status_code == 200
        assert persisted.json()["task_id"] == body["task"]["id"]


def test_input_contract_rejects_missing_facts(tmp_path: Path) -> None:
    settings = Settings(
        root_dir=ROOT_DIR,
        data_dir=tmp_path / "runtime",
        web_dist=tmp_path / "missing-web-dist",
    )
    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/api/workflows/product-content/run",
            json={
                "provider": "demo",
                "inputs": {"category": "服装", "product_name": ""},
            },
        )
        assert response.status_code == 422
        assert "商品名称" in response.json()["detail"]
        assert client.get("/api/tasks").json()["items"] == []


def test_configured_provider_requires_private_server_config(tmp_path: Path) -> None:
    settings = Settings(
        root_dir=ROOT_DIR,
        data_dir=tmp_path / "runtime",
        web_dist=tmp_path / "missing-web-dist",
        provider="demo",
        api_key="must-never-be-returned",
    )
    with TestClient(create_app(settings)) as client:
        status_response = client.get("/api/status")
        assert status_response.status_code == 200
        assert "must-never-be-returned" not in status_response.text
        assert status_response.json()["configured_model_ready"] is False

        response = client.post(
            "/api/workflows/product-content/run",
            json={
                "provider": "configured",
                "inputs": {
                    "category": "眼镜",
                    "product_name": "测试镜框",
                    "selling_points": "方圆框型",
                    "tone": "简洁有力",
                },
            },
        )
        assert response.status_code == 400
        tasks = client.get("/api/tasks").json()["items"]
        assert len(tasks) == 1
        assert tasks[0]["status"] == "failed"
        assert "must-never-be-returned" not in str(tasks[0])


def test_unknown_workflow_and_artifact_return_404(tmp_path: Path) -> None:
    settings = Settings(
        root_dir=ROOT_DIR,
        data_dir=tmp_path / "runtime",
        web_dist=tmp_path / "missing-web-dist",
    )
    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/api/workflows/not-found/run",
            json={"provider": "demo", "inputs": {}},
        )
        assert response.status_code == 404
        assert client.get("/api/artifacts/not-found").status_code == 404


def test_configured_model_branch_creates_artifact(
    tmp_path: Path, monkeypatch
) -> None:
    class FakeConfiguredProvider:
        async def generate(self, messages: list[dict[str, str]]) -> str:
            assert messages[0]["role"] == "system"
            return """
            {
              "product_title": "模型生成标题",
              "selling_points": ["基于输入的卖点"],
              "social_post": "模型生成的待审核文案。",
              "short_video_script": [
                {
                  "scene": "开场",
                  "visual": "展示商品",
                  "voiceover": "介绍商品"
                }
              ],
              "review_notes": ["核验商品事实"]
            }
            """

    monkeypatch.setattr(
        main_module,
        "configured_provider",
        lambda settings: FakeConfiguredProvider(),
    )
    settings = Settings(
        root_dir=ROOT_DIR,
        data_dir=tmp_path / "runtime",
        web_dist=tmp_path / "missing-web-dist",
        provider="openai-compatible",
        base_url="https://model.example/v1",
        api_key="test-placeholder",
        model="example-model",
    )
    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/api/workflows/product-content/run",
            json={
                "provider": "configured",
                "inputs": {
                    "category": "鞋包",
                    "product_name": "测试托特包",
                    "selling_points": "顶部拉链闭合",
                    "tone": "克制专业",
                },
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["task"]["provider"] == "openai-compatible"
        assert body["artifact"]["content"]["generation_mode"] == "configured-model"
        assert body["artifact"]["content"]["product_title"] == "模型生成标题"
