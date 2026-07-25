from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_compose_defaults_to_demo_without_env_file() -> None:
    compose = yaml.safe_load(
        (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    )
    service = compose["services"]["aicowork"]
    assert "env_file" not in service
    assert service["ports"] == ["8787:8787"]
    assert service["environment"]["AICOWORK_PROVIDER"] == (
        "${AICOWORK_PROVIDER:-demo}"
    )
    assert service["environment"]["AICOWORK_API_KEY"] == (
        "${AICOWORK_API_KEY:-}"
    )
    assert service["healthcheck"]["retries"] == 5
    assert service["volumes"] == ["aicowork-data:/app/runtime"]


def test_dockerfile_is_multistage_and_does_not_copy_env() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "FROM node:22-alpine AS web-builder" in dockerfile
    assert "FROM python:3.12-slim AS runtime" in dockerfile
    assert "pnpm install --frozen-lockfile" in dockerfile
    assert "COPY .env" not in dockerfile
    assert 'EXPOSE 8787' in dockerfile


def test_github_workflows_require_container_smoke() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "container-smoke:" in ci
    assert "docker compose up --build --detach" in ci
    assert "docker compose up --build --detach" in release
