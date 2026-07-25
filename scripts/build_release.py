from __future__ import annotations

import argparse
import hashlib
import json
import stat
import zipfile
from pathlib import Path

try:
    from .verify_public_tree import ROOT, verify_public_tree
except ImportError:
    from verify_public_tree import ROOT, verify_public_tree


VERSION = "0.1.0-alpha"
ARCHIVE_ROOT = f"aicowork-fashion-{VERSION}"
FIXED_ZIP_TIME = (2026, 7, 24, 0, 0, 0)


def build_archive(output_path: Path) -> dict[str, object]:
    files, errors = verify_public_tree()
    if errors:
        raise RuntimeError("\n".join(errors))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in files:
            relative = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(
                filename=f"{ARCHIVE_ROOT}/{relative}",
                date_time=FIXED_ZIP_TIME,
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (
                stat.S_IFREG | (0o755 if path.suffix == ".sh" else 0o644)
            ) << 16
            archive.writestr(info, path.read_bytes())

    digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
    checksum_path = output_path.with_suffix(f"{output_path.suffix}.sha256")
    checksum_path.write_text(
        f"{digest}  {output_path.name}\n",
        encoding="utf-8",
    )

    return {
        "archive": str(output_path),
        "archive_root": ARCHIVE_ROOT,
        "files": len(files),
        "bytes": output_path.stat().st_size,
        "sha256": digest,
        "checksum_file": str(checksum_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the allowlisted AiCowork Fashion source archive."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "release" / f"{ARCHIVE_ROOT}.zip",
    )
    parser.add_argument(
        "--tag",
        help=f"Optional release tag; when set it must equal v{VERSION}.",
    )
    args = parser.parse_args()
    if args.tag and args.tag != f"v{VERSION}":
        parser.error(
            f"release tag {args.tag!r} does not match source version v{VERSION}"
        )
    result = build_archive(args.output.expanduser().resolve())
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
