from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class WorkflowInputError(ValueError):
    """The workflow input is missing or invalid."""


class WorkflowOutputError(ValueError):
    """The model output cannot be converted into the workflow contract."""


class WorkflowHandler(ABC):
    def __init__(self, workflow_dir: Path, manifest: dict[str, Any]) -> None:
        self.workflow_dir = workflow_dir
        self.manifest = manifest

    @abstractmethod
    def validate_inputs(self, raw_inputs: dict[str, Any]) -> dict[str, Any]:
        """Validate and normalize public task inputs."""

    @abstractmethod
    def demo_output(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Return deterministic output without contacting a model."""

    @abstractmethod
    def build_messages(self, inputs: dict[str, Any]) -> list[dict[str, str]]:
        """Build an OpenAI-compatible messages payload."""

    @abstractmethod
    def parse_model_output(self, raw_content: str) -> dict[str, Any]:
        """Convert model text into the public output contract."""

    @abstractmethod
    def artifact_title(
        self, inputs: dict[str, Any], output: dict[str, Any]
    ) -> str:
        """Create a human-readable artifact title."""
