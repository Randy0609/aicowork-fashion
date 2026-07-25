from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _read_env_file(path: Path) -> None:
    """Load a small .env file without overriding process environment variables."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, raw_value = line.partition("=")
        key = key.strip()
        value = raw_value.strip().strip("'\"")
        if key:
            os.environ.setdefault(key, value)


@dataclass(frozen=True, slots=True)
class Settings:
    root_dir: Path
    data_dir: Path
    web_dist: Path
    provider: str = "demo"
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = ""
    cors_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )

    @classmethod
    def from_env(cls) -> "Settings":
        root_dir = Path(__file__).resolve().parents[3]
        _read_env_file(root_dir / ".env")

        data_dir = Path(os.getenv("AICOWORK_DATA_DIR", str(root_dir / "runtime")))
        web_dist = Path(
            os.getenv("AICOWORK_WEB_DIST", str(root_dir / "apps" / "web" / "dist"))
        )
        origins = tuple(
            item.strip()
            for item in os.getenv(
                "AICOWORK_CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173",
            ).split(",")
            if item.strip()
        )
        return cls(
            root_dir=root_dir,
            data_dir=data_dir.expanduser().resolve(),
            web_dist=web_dist.expanduser().resolve(),
            provider=os.getenv("AICOWORK_PROVIDER", "demo").strip().lower() or "demo",
            base_url=os.getenv(
                "AICOWORK_BASE_URL", "https://api.openai.com/v1"
            ).strip(),
            api_key=os.getenv("AICOWORK_API_KEY", "").strip(),
            model=os.getenv("AICOWORK_MODEL", "").strip(),
            cors_origins=origins,
        )

    @property
    def configured_model_ready(self) -> bool:
        return (
            self.provider == "openai-compatible"
            and bool(self.base_url)
            and bool(self.api_key)
            and bool(self.model)
        )
