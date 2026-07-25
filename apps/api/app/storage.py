from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.database_path = data_dir / "aicowork.db"
        self._lock = RLock()

    def initialize(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    status TEXT NOT NULL,
                    inputs_json TEXT NOT NULL,
                    artifact_id TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    workflow_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_created_at
                ON tasks(created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_artifacts_created_at
                ON artifacts(created_at DESC);
                """
            )

    def create_task(
        self, workflow_id: str, provider: str, inputs: dict[str, Any]
    ) -> dict[str, Any]:
        task_id = f"task_{uuid4().hex}"
        created_at = utc_now()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO tasks (
                    id, workflow_id, provider, status, inputs_json, created_at
                ) VALUES (?, ?, ?, 'running', ?, ?)
                """,
                (
                    task_id,
                    workflow_id,
                    provider,
                    json.dumps(inputs, ensure_ascii=False),
                    created_at,
                ),
            )
        return self.get_task(task_id)

    def complete_task(
        self,
        task_id: str,
        workflow_id: str,
        title: str,
        content: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        artifact_id = f"artifact_{uuid4().hex}"
        completed_at = utc_now()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO artifacts (
                    id, task_id, workflow_id, title, content_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_id,
                    task_id,
                    workflow_id,
                    title,
                    json.dumps(content, ensure_ascii=False),
                    completed_at,
                ),
            )
            connection.execute(
                """
                UPDATE tasks
                SET status = 'completed', artifact_id = ?, completed_at = ?
                WHERE id = ?
                """,
                (artifact_id, completed_at, task_id),
            )
        return self.get_task(task_id), self.get_artifact(artifact_id)

    def fail_task(self, task_id: str, error: str) -> dict[str, Any]:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                UPDATE tasks
                SET status = 'failed', error = ?, completed_at = ?
                WHERE id = ?
                """,
                (error[:500], utc_now(), task_id),
            )
        return self.get_task(task_id)

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
        return self._task_row(row) if row else None

    def list_tasks(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._task_row(row) for row in rows]

    def get_artifact(self, artifact_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
            ).fetchone()
        return self._artifact_row(row) if row else None

    def list_artifacts(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM artifacts ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._artifact_row(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _task_row(row: sqlite3.Row) -> dict[str, Any]:
        payload = dict(row)
        payload["inputs"] = json.loads(payload.pop("inputs_json"))
        return payload

    @staticmethod
    def _artifact_row(row: sqlite3.Row) -> dict[str, Any]:
        payload = dict(row)
        payload["content"] = json.loads(payload.pop("content_json"))
        return payload
