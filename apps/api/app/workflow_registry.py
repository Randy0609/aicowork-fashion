from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .workflow_base import WorkflowHandler


@dataclass(frozen=True, slots=True)
class RegisteredWorkflow:
    workflow_id: str
    directory: Path
    manifest: dict[str, Any]
    handler: WorkflowHandler

    def public_manifest(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in self.manifest.items()
            if key not in {"handler"}
        }


class WorkflowRegistry:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.workflows_dir = root_dir / "workflows"
        self._items: dict[str, RegisteredWorkflow] = {}

    def load(self) -> None:
        items: dict[str, RegisteredWorkflow] = {}
        if not self.workflows_dir.is_dir():
            raise RuntimeError(f"Workflow directory not found: {self.workflows_dir}")

        for manifest_path in sorted(self.workflows_dir.glob("*/manifest.json")):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            workflow_id = str(manifest.get("id") or "").strip()
            handler_ref = str(manifest.get("handler") or "").strip()
            if not workflow_id or not handler_ref or ":" not in handler_ref:
                raise RuntimeError(f"Invalid workflow manifest: {manifest_path}")
            if workflow_id in items:
                raise RuntimeError(f"Duplicate workflow id: {workflow_id}")

            module_name, class_name = handler_ref.split(":", 1)
            module = importlib.import_module(module_name)
            handler_type = getattr(module, class_name)
            handler = handler_type(manifest_path.parent, manifest)
            if not isinstance(handler, WorkflowHandler):
                raise RuntimeError(
                    f"Handler {handler_ref} must inherit WorkflowHandler"
                )
            items[workflow_id] = RegisteredWorkflow(
                workflow_id=workflow_id,
                directory=manifest_path.parent,
                manifest=manifest,
                handler=handler,
            )
        if not items:
            raise RuntimeError("No workflows were discovered")
        self._items = items

    def list(self) -> list[RegisteredWorkflow]:
        return list(self._items.values())

    def get(self, workflow_id: str) -> RegisteredWorkflow | None:
        return self._items.get(workflow_id)


def load_categories(root_dir: Path) -> list[dict[str, Any]]:
    categories_dir = root_dir / "configs" / "categories"
    categories: list[dict[str, Any]] = []
    for path in sorted(categories_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["config_file"] = path.name
        categories.append(payload)
    return categories
