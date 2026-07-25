from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_url(url: str, timeout_seconds: float = 10) -> bytes:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return response.read()
        except (OSError, urllib.error.URLError) as exc:
            last_error = exc
            time.sleep(0.1)
    raise RuntimeError(f"服务未在限定时间内就绪：{last_error}")


def smoke_boot(require_web: bool = False) -> None:
    port = free_port()
    with tempfile.TemporaryDirectory(prefix="aicowork-smoke-") as data_dir:
        env = os.environ.copy()
        env["AICOWORK_PROVIDER"] = "demo"
        env["AICOWORK_API_KEY"] = ""
        env["AICOWORK_MODEL"] = ""
        env["AICOWORK_DATA_DIR"] = data_dir
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "apps.api.app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            health = wait_for_url(f"http://127.0.0.1:{port}/api/health")
            if b'"status":"ok"' not in health:
                raise RuntimeError("健康检查响应不符合合同")
            if require_web:
                homepage = wait_for_url(f"http://127.0.0.1:{port}/")
                if b"AiCowork Fashion" not in homepage:
                    raise RuntimeError("前端首页未由 API 服务正常托管")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        if process.returncode not in {0, -15}:
            error = (process.stderr.read() if process.stderr else "").strip()
            raise RuntimeError(f"服务退出异常：{error[-500:]}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Boot and probe the local workbench.")
    parser.add_argument("--require-web", action="store_true")
    args = parser.parse_args()
    smoke_boot(require_web=args.require_web)
    print("smoke boot passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
