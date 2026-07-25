from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from apps.api.app.workflow_base import (
    WorkflowHandler,
    WorkflowInputError,
    WorkflowOutputError,
)


MAX_FIELD_LENGTH = 2000


def _clean_text(value: Any, *, limit: int = MAX_FIELD_LENGTH) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:limit]


def _split_points(value: str) -> list[str]:
    parts = [
        _clean_text(item, limit=160)
        for item in re.split(r"[\n；;。]+", value)
        if _clean_text(item)
    ]
    return parts[:5]


class ProductContentWorkflow(WorkflowHandler):
    def __init__(self, workflow_dir: Path, manifest: dict[str, Any]) -> None:
        super().__init__(workflow_dir, manifest)
        self.system_prompt = (workflow_dir / "prompt.md").read_text(encoding="utf-8")

    def validate_inputs(self, raw_inputs: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(raw_inputs, dict):
            raise WorkflowInputError("inputs 必须是对象")
        normalized = {
            "category": _clean_text(raw_inputs.get("category"), limit=80),
            "product_name": _clean_text(raw_inputs.get("product_name"), limit=120),
            "material": _clean_text(raw_inputs.get("material"), limit=300),
            "target_customer": _clean_text(
                raw_inputs.get("target_customer"), limit=300
            ),
            "selling_points": _clean_text(
                raw_inputs.get("selling_points"), limit=1200
            ),
            "tone": _clean_text(raw_inputs.get("tone"), limit=40)
            or "克制专业",
        }
        missing = [
            label
            for field, label in (
                ("category", "品类"),
                ("product_name", "商品名称"),
                ("selling_points", "已核实卖点"),
            )
            if not normalized[field]
        ]
        if missing:
            raise WorkflowInputError(f"请填写：{'、'.join(missing)}")
        if normalized["tone"] not in {"克制专业", "轻松自然", "简洁有力"}:
            raise WorkflowInputError("表达风格不在允许范围内")
        return normalized

    def demo_output(self, inputs: dict[str, Any]) -> dict[str, Any]:
        product_name = inputs["product_name"]
        category = inputs["category"]
        material = inputs["material"]
        audience = inputs["target_customer"]
        points = _split_points(inputs["selling_points"])
        if not points:
            points = ["已核实卖点待商家补充"]

        title_parts = [product_name, category]

        audience_line = f"这份草稿面向{audience}。" if audience else ""
        point_text = "；".join(points[:3])
        social_post = (
            f"这次整理的是「{product_name}」。{point_text}。"
            f"{audience_line}以上内容来自商家填写的商品资料，发布前请再次核对。"
        )
        review_notes = ["确认商品名称、材质与卖点均与实物及商品页面一致"]
        if not material:
            review_notes.append("材质与工艺尚未填写")
        if not audience:
            review_notes.append("目标顾客尚未填写")

        return {
            "product_title": "｜".join(title_parts),
            "selling_points": points,
            "social_post": social_post,
            "short_video_script": [
                {
                    "scene": "开场",
                    "visual": f"展示{product_name}整体外观",
                    "voiceover": f"今天看一件{category}商品：{product_name}。",
                },
                {
                    "scene": "细节",
                    "visual": "依次展示与已核实卖点对应的细节",
                    "voiceover": point_text,
                },
                {
                    "scene": "收尾",
                    "visual": "回到商品整体，保留品牌自行补充的行动提示",
                    "voiceover": "具体信息请以商家最终核实后的商品页面为准。",
                },
            ],
            "review_notes": review_notes,
            "generation_mode": "demo",
        }

    def build_messages(self, inputs: dict[str, Any]) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "task": "根据以下已核实资料生成商品内容草稿",
                        "product": inputs,
                    },
                    ensure_ascii=False,
                ),
            },
        ]

    def parse_model_output(self, raw_content: str) -> dict[str, Any]:
        content = raw_content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start < 0 or end <= start:
                raise WorkflowOutputError("模型没有返回合法 JSON")
            try:
                payload = json.loads(content[start : end + 1])
            except json.JSONDecodeError as exc:
                raise WorkflowOutputError("模型返回的 JSON 无法解析") from exc
        if not isinstance(payload, dict):
            raise WorkflowOutputError("模型输出必须是 JSON 对象")

        title = _clean_text(payload.get("product_title"), limit=200)
        social_post = _clean_text(payload.get("social_post"), limit=4000)
        points = payload.get("selling_points")
        script = payload.get("short_video_script")
        notes = payload.get("review_notes")
        if not title or not social_post:
            raise WorkflowOutputError("模型输出缺少标题或社媒文案")
        if not isinstance(points, list) or not points:
            raise WorkflowOutputError("模型输出缺少卖点列表")
        if not isinstance(script, list) or not script:
            raise WorkflowOutputError("模型输出缺少短视频脚本")

        clean_script: list[dict[str, str]] = []
        for item in script[:8]:
            if not isinstance(item, dict):
                continue
            clean_script.append(
                {
                    "scene": _clean_text(item.get("scene"), limit=100),
                    "visual": _clean_text(item.get("visual"), limit=500),
                    "voiceover": _clean_text(item.get("voiceover"), limit=800),
                }
            )
        if not clean_script:
            raise WorkflowOutputError("短视频脚本结构无效")

        return {
            "product_title": title,
            "selling_points": [
                _clean_text(item, limit=300) for item in points[:8] if _clean_text(item)
            ],
            "social_post": social_post,
            "short_video_script": clean_script,
            "review_notes": [
                _clean_text(item, limit=300)
                for item in (notes if isinstance(notes, list) else [])
                if _clean_text(item)
            ]
            or ["发布前请由商家核验所有商品事实和承诺"],
            "generation_mode": "configured-model",
        }

    def artifact_title(
        self, inputs: dict[str, Any], output: dict[str, Any]
    ) -> str:
        return f"{inputs['product_name']} · 商品内容"
