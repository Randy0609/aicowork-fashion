from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .providers import (
    ProviderCallError,
    ProviderConfigError,
    configured_provider,
)
from .settings import Settings
from .storage import Store
from .workflow_base import WorkflowInputError, WorkflowOutputError
from .workflow_registry import WorkflowRegistry, load_categories


class RunWorkflowRequest(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)
    provider: Literal["demo", "configured"] = "demo"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    store = Store(settings.data_dir)
    registry = WorkflowRegistry(settings.root_dir)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        store.initialize()
        registry.load()
        yield

    app = FastAPI(
        title="AiCowork Fashion API",
        version="0.1.0-alpha",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": "0.1.0-alpha"}

    @app.get("/api/status")
    def status() -> dict[str, Any]:
        return {
            "version": "0.1.0-alpha",
            "default_provider": settings.provider,
            "configured_model_ready": settings.configured_model_ready,
            "configured_model": settings.model if settings.configured_model_ready else None,
            "data_store": "sqlite",
        }

    @app.get("/api/categories")
    def categories() -> dict[str, Any]:
        return {"items": load_categories(settings.root_dir)}

    @app.get("/api/workflows")
    def workflows() -> dict[str, Any]:
        return {
            "items": [item.public_manifest() for item in registry.list()]
        }

    @app.post("/api/workflows/{workflow_id}/run")
    async def run_workflow(
        workflow_id: str, request: RunWorkflowRequest
    ) -> dict[str, Any]:
        workflow = registry.get(workflow_id)
        if workflow is None:
            raise HTTPException(status_code=404, detail="工作流不存在")
        try:
            inputs = workflow.handler.validate_inputs(request.inputs)
        except WorkflowInputError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        provider_label = (
            "demo" if request.provider == "demo" else settings.provider
        )
        task = store.create_task(workflow_id, provider_label, inputs)

        try:
            if request.provider == "demo":
                output = workflow.handler.demo_output(inputs)
            else:
                provider = configured_provider(settings)
                raw_content = await provider.generate(
                    workflow.handler.build_messages(inputs)
                )
                output = workflow.handler.parse_model_output(raw_content)
            title = workflow.handler.artifact_title(inputs, output)
            completed_task, artifact = store.complete_task(
                task_id=task["id"],
                workflow_id=workflow_id,
                title=title,
                content=output,
            )
            return {"task": completed_task, "artifact": artifact}
        except ProviderConfigError as exc:
            store.fail_task(task["id"], str(exc))
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except (ProviderCallError, WorkflowOutputError) as exc:
            store.fail_task(task["id"], str(exc))
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except Exception as exc:
            store.fail_task(task["id"], "工作流执行失败")
            raise HTTPException(status_code=500, detail="工作流执行失败") from exc

    @app.get("/api/tasks")
    def tasks(limit: int = Query(default=50, ge=1, le=200)) -> dict[str, Any]:
        return {"items": store.list_tasks(limit)}

    @app.get("/api/tasks/{task_id}")
    def task(task_id: str) -> dict[str, Any]:
        item = store.get_task(task_id)
        if item is None:
            raise HTTPException(status_code=404, detail="任务不存在")
        return item

    @app.get("/api/artifacts")
    def artifacts(
        limit: int = Query(default=50, ge=1, le=200),
    ) -> dict[str, Any]:
        return {"items": store.list_artifacts(limit)}

    @app.get("/api/artifacts/{artifact_id}")
    def artifact(artifact_id: str) -> dict[str, Any]:
        item = store.get_artifact(artifact_id)
        if item is None:
            raise HTTPException(status_code=404, detail="产物不存在")
        return item

    if settings.web_dist.is_dir():
        app.mount(
            "/",
            StaticFiles(directory=settings.web_dist, html=True),
            name="web",
        )

    app.state.settings = settings
    app.state.store = store
    app.state.registry = registry
    return app


app = create_app()
