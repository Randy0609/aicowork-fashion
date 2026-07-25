from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ALLOWED_ROOT_FILES = {
    ".dockerignore",
    ".env.example",
    ".gitignore",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "Dockerfile",
    "LICENSE",
    "PROVENANCE.md",
    "README.md",
    "SECURITY.md",
    "THIRD_PARTY_NOTICES.md",
    "TRADEMARKS.md",
    "docker-compose.yml",
}

ALLOWED_ROOT_DIRS = {
    ".github",
    "apps",
    "configs",
    "data",
    "docs",
    "scripts",
    "tests",
    "workflows",
}

IGNORED_NAMES = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "coverage",
    "dist",
    "node_modules",
    "release",
    "runtime",
}

FORBIDDEN_FILENAMES = {
    ".env",
    "id_ed25519",
    "id_rsa",
}

FORBIDDEN_SUFFIXES = {
    ".csv",
    ".db",
    ".duckdb",
    ".key",
    ".log",
    ".p12",
    ".pem",
    ".pyc",
    ".xls",
    ".xlsx",
}

TEXT_SUFFIXES = {
    "",
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

MAX_PUBLIC_FILE_BYTES = 5 * 1024 * 1024

HIGH_CONFIDENCE_TEXT_PATTERNS = {
    "macOS 用户绝对路径": re.compile("/" + "Users" + "/"),
    "私钥头": re.compile("BEGIN " + r"(?:RSA |OPENSSH |EC )?" + "PRIVATE KEY"),
    "高置信度 API token": re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
}


def is_ignored(path: Path) -> bool:
    return any(part in IGNORED_NAMES for part in path.relative_to(ROOT).parts)


def collect_public_files() -> list[Path]:
    files: list[Path] = []
    for entry in sorted(ROOT.iterdir(), key=lambda item: item.name):
        if entry.name in IGNORED_NAMES:
            continue
        if entry.is_symlink():
            files.append(entry)
            continue
        if entry.is_file():
            if entry.name in ALLOWED_ROOT_FILES:
                files.append(entry)
            continue
        if entry.is_dir() and entry.name in ALLOWED_ROOT_DIRS:
            for path in sorted(entry.rglob("*")):
                if path.is_file() and not is_ignored(path):
                    files.append(path)
    return files


def verify_public_tree() -> tuple[list[Path], list[str]]:
    errors: list[str] = []
    files = collect_public_files()
    relative_files = {path.relative_to(ROOT).as_posix() for path in files}

    for required in (
        ".env.example",
        "LICENSE",
        "README.md",
        "apps/api/app/main.py",
        "apps/web/package.json",
        "apps/web/pnpm-lock.yaml",
        "docker-compose.yml",
        "workflows/product_content/manifest.json",
    ):
        if required not in relative_files:
            errors.append(f"缺少发布必需文件：{required}")

    for entry in ROOT.iterdir():
        if entry.name in IGNORED_NAMES:
            continue
        if entry.is_file() and entry.name not in ALLOWED_ROOT_FILES:
            errors.append(f"根目录文件不在 allowlist：{entry.name}")
        if entry.is_dir() and entry.name not in ALLOWED_ROOT_DIRS:
            errors.append(f"根目录目录不在 allowlist：{entry.name}/")

    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        if path.is_symlink():
            errors.append(f"不允许发布符号链接：{relative}")
            continue
        if path.name in FORBIDDEN_FILENAMES:
            errors.append(f"不允许发布文件：{relative}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"不允许发布文件类型：{relative}")
        if path.stat().st_size > MAX_PUBLIC_FILE_BYTES:
            errors.append(f"公开文件超过 5 MiB：{relative}")
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"文本文件不是 UTF-8：{relative}")
            continue
        for label, pattern in HIGH_CONFIDENCE_TEXT_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{label}：{relative}")

    env_example = ROOT / ".env.example"
    if env_example.is_file():
        for line in env_example.read_text(encoding="utf-8").splitlines():
            if line.startswith("AICOWORK_API_KEY=") and line != "AICOWORK_API_KEY=":
                errors.append(".env.example 不得包含非空 API Key")

    return files, errors


def main() -> int:
    files, errors = verify_public_tree()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    total_bytes = sum(path.stat().st_size for path in files)
    print(f"public tree verified: {len(files)} files, {total_bytes} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
