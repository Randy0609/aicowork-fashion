from __future__ import annotations

import json
from pathlib import Path

import pytest

from apps.api.app.workflow_base import WorkflowInputError, WorkflowOutputError
from workflows.product_content.handler import ProductContentWorkflow


WORKFLOW_DIR = Path(__file__).resolve().parents[1] / "workflows" / "product_content"
MANIFEST = json.loads(
    (WORKFLOW_DIR / "manifest.json").read_text(encoding="utf-8")
)


def workflow() -> ProductContentWorkflow:
    return ProductContentWorkflow(WORKFLOW_DIR, MANIFEST)


def test_model_output_contract_accepts_fenced_json() -> None:
    raw = """```json
    {
      "product_title": "简洁标题",
      "selling_points": ["已核实卖点"],
      "social_post": "根据已填写资料整理的文案。",
      "short_video_script": [
        {"scene": "开场", "visual": "展示商品", "voiceover": "介绍商品"}
      ],
      "review_notes": ["核验材质"]
    }
    ```"""
    output = workflow().parse_model_output(raw)
    assert output["product_title"] == "简洁标题"
    assert output["generation_mode"] == "configured-model"


def test_model_output_contract_rejects_plain_text() -> None:
    with pytest.raises(WorkflowOutputError):
        workflow().parse_model_output("这不是 JSON")


def test_input_length_and_tone_are_guarded() -> None:
    with pytest.raises(WorkflowInputError):
        workflow().validate_inputs(
            {
                "category": "服装",
                "product_name": "测试商品",
                "selling_points": "已核实卖点",
                "tone": "夸张承诺",
            }
        )
