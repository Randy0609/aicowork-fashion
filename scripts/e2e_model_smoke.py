from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

try:
    from .smoke_boot import free_port, wait_for_url
except ImportError:
    from smoke_boot import free_port, wait_for_url


ROOT = Path(__file__).resolve().parents[1]


class MockModelHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/v1/chat/completions":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            request_body = json.loads(self.rfile.read(length))
        except (ValueError, TypeError):
            self.send_error(400)
            return
        if (
            request_body.get("model") != "local-e2e-model"
            or not request_body.get("messages")
            or self.headers.get("Authorization") != "Bearer local-e2e-placeholder"
        ):
            self.send_error(400)
            return

        model_content = {
            "product_title": "本地协议测试标题",
            "selling_points": ["只使用输入中的已核实卖点"],
            "social_post": "这是通过真实 HTTP 兼容接口返回的本地测试文案。",
            "short_video_script": [
                {
                    "scene": "开场",
                    "visual": "展示模拟商品",
                    "voiceover": "介绍模拟商品",
                }
            ],
            "review_notes": ["发布前核验商品事实"],
        }
        response_body = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(
                                model_content,
                                ensure_ascii=False,
                            ),
                        }
                    }
                ]
            },
            ensure_ascii=False,
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read())


def get_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read())


def e2e_model_smoke() -> None:
    model_server = ThreadingHTTPServer(("127.0.0.1", 0), MockModelHandler)
    model_port = int(model_server.server_address[1])
    model_thread = threading.Thread(
        target=model_server.serve_forever,
        daemon=True,
    )
    model_thread.start()

    app_port = free_port()
    with tempfile.TemporaryDirectory(prefix="aicowork-model-e2e-") as data_dir:
        env = os.environ.copy()
        env["AICOWORK_PROVIDER"] = "openai-compatible"
        env["AICOWORK_BASE_URL"] = f"http://127.0.0.1:{model_port}/v1"
        env["AICOWORK_API_KEY"] = "local-e2e-placeholder"
        env["AICOWORK_MODEL"] = "local-e2e-model"
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
                str(app_port),
            ],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            wait_for_url(f"http://127.0.0.1:{app_port}/api/health")
            result = post_json(
                f"http://127.0.0.1:{app_port}/api/workflows/product-content/run",
                {
                    "provider": "configured",
                    "inputs": {
                        "category": "服装",
                        "product_name": "协议测试商品",
                        "selling_points": "已核实卖点",
                        "tone": "克制专业",
                    },
                },
            )
            task = result["task"]
            artifact = result["artifact"]
            if task["status"] != "completed":
                raise RuntimeError("配置模型任务没有完成")
            if task["provider"] != "openai-compatible":
                raise RuntimeError("任务没有经过配置模型分支")
            if artifact["content"]["generation_mode"] != "configured-model":
                raise RuntimeError("模型结果没有进入配置模型产物合同")
            artifacts = get_json(f"http://127.0.0.1:{app_port}/api/artifacts")
            if len(artifacts["items"]) != 1:
                raise RuntimeError("配置模型产物没有持久化")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            model_server.shutdown()
            model_server.server_close()
            model_thread.join(timeout=5)
        if process.returncode not in {0, -15}:
            error = (process.stderr.read() if process.stderr else "").strip()
            raise RuntimeError(f"工作台服务退出异常：{error[-500:]}")


def main() -> int:
    e2e_model_smoke()
    print("configured model HTTP e2e passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
