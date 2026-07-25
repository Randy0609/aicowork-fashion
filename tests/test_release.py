from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

from scripts.build_release import ARCHIVE_ROOT, build_archive
from scripts.verify_public_tree import ROOT, collect_public_files, verify_public_tree


def test_public_tree_is_allowlisted() -> None:
    files, errors = verify_public_tree()
    assert errors == []
    relative = {path.relative_to(ROOT).as_posix() for path in files}
    assert "README.md" in relative
    assert "apps/api/app/main.py" in relative
    assert "apps/web/src/App.tsx" in relative
    assert "docs/assets/workbench-preview.jpg" in relative
    assert all("runtime/" not in item for item in relative)
    assert all("node_modules/" not in item for item in relative)
    assert all("__pycache__/" not in item for item in relative)


def test_release_archive_contains_only_verified_files(tmp_path: Path) -> None:
    output = tmp_path / "release.zip"
    result = build_archive(output)
    assert result["files"] == len(collect_public_files())
    assert result["bytes"] > 0
    assert result["sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    checksum_path = Path(str(result["checksum_file"]))
    assert checksum_path.read_text(encoding="utf-8") == (
        f"{result['sha256']}  {output.name}\n"
    )

    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        assert f"{ARCHIVE_ROOT}/README.md" in names
        assert f"{ARCHIVE_ROOT}/apps/api/app/main.py" in names
        assert f"{ARCHIVE_ROOT}/apps/web/pnpm-lock.yaml" in names
        assert all(not name.endswith("/.env") for name in names)
        assert all("/runtime/" not in name for name in names)
        assert all("/node_modules/" not in name for name in names)
        assert all("/.venv/" not in name for name in names)


def test_release_archive_is_reproducible(tmp_path: Path) -> None:
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    build_archive(first)
    build_archive(second)
    assert first.read_bytes() == second.read_bytes()
