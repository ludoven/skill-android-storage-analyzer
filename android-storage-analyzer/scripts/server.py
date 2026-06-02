#!/usr/bin/env python3
"""Serve the Android storage report with a guarded one-click adb execute API.

Starts on 127.0.0.1 + a random port + a random per-session token. The page is
interactive only for allowlisted green-tier cleanup actions provided in the
analysis JSON. Stop with Ctrl+C.
"""

from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "report_template.html")
TOKEN = secrets.token_urlsafe(24)

DATA = {}
TPL = ""
ALLOW = {}


def load(src: str):
    with open(src, encoding="utf-8") as handle:
        data = json.load(handle)
    with open(TEMPLATE, encoding="utf-8") as handle:
        tpl = handle.read()

    allow = {}
    for idx, item in enumerate(data.get("green", [])):
        item_key = f"green-{idx}"
        for action_index, action in enumerate(item.get("cleanup_actions") or []):
            command = action.get("command", "").strip()
            if not command:
                continue
            allow[(item_key, action_index)] = {
                "command": command,
                "label": action.get("label", "执行清理"),
            }
    return data, tpl, allow


def adb_run(serial: str | None, command: str) -> subprocess.CompletedProcess[str]:
    args = ["adb"]
    if serial:
        args.extend(["-s", serial])
    args.extend(["shell", "sh", "-c", command])
    return subprocess.run(args, text=True, capture_output=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code: int, body: str, ctype: str = "application/json"):
        payload = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            self._send(404, "not found", "text/plain")
            return
        blob = json.dumps(DATA, ensure_ascii=False)
        cfg = json.dumps({"token": TOKEN, "endpoint": "/action"})
        html = TPL.replace("__REPORT_DATA__", blob).replace("__DELETE_CONFIG__", cfg)
        self._send(200, html, "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/action":
            self._send(404, json.dumps({"ok": False, "error": "not found"}))
            return
        host = (self.headers.get("Host") or "").split(":")[0]
        if host not in ("127.0.0.1", "localhost"):
            self._send(403, json.dumps({"ok": False, "error": "host 不被允许"}))
            return
        try:
            req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except Exception:
            self._send(400, json.dumps({"ok": False, "error": "请求格式错误"}))
            return
        if req.get("token") != TOKEN:
            self._send(403, json.dumps({"ok": False, "error": "token 校验失败"}))
            return

        item_key = req.get("item")
        action_index = req.get("action_index")
        key = (item_key, action_index)
        action = ALLOW.get(key)
        if action is None:
            self._send(403, json.dumps({"ok": False, "error": "动作不在白名单"}))
            return

        serial = ((DATA.get("system") or {}).get("serial") or "").strip() or None
        result = adb_run(serial, action["command"])
        if result.returncode != 0:
            error = (result.stderr or result.stdout or "adb shell 执行失败").strip()
            self._send(500, json.dumps({"ok": False, "error": error}))
            return

        self._send(200, json.dumps({
            "ok": True,
            "stdout": (result.stdout or "").strip(),
            "label": action["label"],
        }))


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    global DATA, TPL, ALLOW
    DATA, TPL, ALLOW = load(sys.argv[1])
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/"
    print("Android 存储报告服务已启动：" + url)
    print(f"可执行绿灯动作 {len(ALLOW)} 个")
    print("用完按 Ctrl+C 停止服务")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止服务。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
