"""Sorty's local server: the kiosk screen talks to this, this talks to the brain.

Standard library only, so it runs on anything with Python (a laptop, a
Raspberry Pi behind the bin). Serves the kiosk at / and the API at /api/*.

    python -m server.app           (from the sorty folder)
"""
from __future__ import annotations

import json
import mimetypes
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from brain import Brain, get_settings, has_api_key, load_station  # noqa: E402
from brain.mock_brain import MockBrain  # noqa: E402
from brain.persona import simulated_answer  # noqa: E402

KIOSK_DIR = ROOT / "kiosk"
IMAGES_DIR = ROOT / "tests" / "images"
SCENARIOS_FILE = ROOT / "tests" / "scenarios.json"
MAX_BODY = 12 * 1024 * 1024

mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/javascript", ".mjs")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("application/json", ".json")


def load_scenarios() -> dict:
    if not SCENARIOS_FILE.exists():
        return {}
    data = json.loads(SCENARIOS_FILE.read_text(encoding="utf-8"))
    return {s["id"]: s for s in data.get("scenarios", [])}


class App:
    """Holds the brain and the demo data; one per server process."""

    def __init__(self, force_mock: bool = False) -> None:
        import os
        self.settings = get_settings()
        self.station = load_station(self.settings.station_id)
        self.scenarios = load_scenarios()
        want_mock = force_mock or os.environ.get("SORTY_MODE", "").lower() == "mock" or not has_api_key()
        if want_mock:
            self.brain = MockBrain(self.settings, self.station, self.scenarios)
        else:
            self.brain = Brain(self.settings, station=self.station)
        self.mode = self.brain.mode

    def config(self) -> dict:
        s = self.settings
        return {
            "assistant_name": s.assistant_name,
            "mode": self.mode,
            "model": s.model if self.mode == "live" else None,
            "lang_default": "en",
            "languages": s.languages,
            "station": {"id": self.station["id"], "name": self.station.get("name", ""), "bins": self.station["bins"]},
            "timeouts": {"answer_s": s.answer_timeout_s, "show_s": s.show_timeout_s, "verdict_hold_s": s.verdict_hold_s},
        }

    def demo_scenarios(self) -> list:
        """Scenarios whose images exist, in the shape the kiosk's demo drawer expects."""
        out = []
        for sc in self.scenarios.values():
            frames = {k: v for k, v in sc.get("frames", {}).items() if (IMAGES_DIR / v).exists()}
            if "initial" not in frames:
                continue
            out.append({
                "id": sc["id"], "title": sc["title"], "group": sc.get("group", ""),
                "lang": sc.get("lang", "en"), "why": sc.get("why", ""),
                "frames": {k: f"/demo-images/{v}" for k, v in frames.items()},
            })
        return out

    def demo_answer(self, scenario_id: str, question: str) -> str:
        sc = self.scenarios.get(scenario_id) or {}
        person = sc.get("person", {})
        if person.get("timeouts"):
            return ""
        if person.get("script"):
            return person["script"][0]
        if self.mode != "live":
            return self.brain.mock_answer(scenario_id)
        return simulated_answer(self.brain.llm, self.settings, person.get("facts", ""), question, sc.get("lang", "en"))


class Handler(BaseHTTPRequestHandler):
    server_version = "Sorty/1.0"
    protocol_version = "HTTP/1.1"
    app: App

    # ------------------------------------------------------------- helpers
    def log_message(self, fmt: str, *args) -> None:  # quieter than the default
        if self.path.startswith("/api/"):
            sys.stderr.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

    def _send(self, status: int, body: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status: int, payload) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise ValueError("request too large")
        raw = self.rfile.read(length) if length else b""
        if not raw:
            return {}
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("JSON object expected")
        return data

    def _static(self, base: Path, rel: str) -> None:
        rel = unquote(rel).lstrip("/") or "index.html"
        target = (base / rel).resolve()
        if base.resolve() not in target.parents and target != base.resolve():
            self._json(403, {"error": "forbidden"})
            return
        if target.is_dir():
            target = target / "index.html"
        if not target.is_file():
            if base is KIOSK_DIR and rel == "index.html":
                self._send(200, b"<h1>Sorty server is running</h1><p>The kiosk interface is not in place yet.</p>", "text/html")
            else:
                self._json(404, {"error": "not found"})
            return
        ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/json", "image/svg+xml"):
            ctype += "; charset=utf-8"
        self._send(200, target.read_bytes(), ctype)

    # -------------------------------------------------------------- routes
    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/config":
            self._json(200, self.app.config())
        elif path == "/api/health":
            self._json(200, {"ok": True, "mode": self.app.mode})
        elif path == "/api/demo/scenarios":
            self._json(200, self.app.demo_scenarios())
        elif path.startswith("/api/"):
            self._json(404, {"error": "not found"})
        elif path.startswith("/demo-images/"):
            self._static(IMAGES_DIR, path[len("/demo-images/"):])
        else:
            self._static(KIOSK_DIR, path)

    do_HEAD = do_GET

    def do_POST(self) -> None:
        path = urlparse(self.path).path.rstrip("/")
        try:
            body = self._body()
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"error": f"bad request: {exc}"})
            return
        try:
            parts = [p for p in path.split("/") if p]          # api, session, <id>, reply
            if path == "/api/session":
                if not body.get("image"):
                    self._json(400, {"error": "image is required"})
                    return
                turn = self.app.brain.start(body["image"], str(body.get("lang") or "en"), body.get("demo_scenario") or None)
                self._json(200, turn)
            elif len(parts) == 4 and parts[:2] == ["api", "session"] and parts[3] == "reply":
                self._json(200, self.app.brain.reply(parts[2], body))
            elif len(parts) == 4 and parts[:2] == ["api", "session"] and parts[3] == "end":
                self.app.brain.end(parts[2])
                self._json(200, {})
            elif path == "/api/demo/answer":
                text = self.app.demo_answer(str(body.get("scenario_id", "")), str(body.get("question", "")))
                self._json(200, {"text": text})
            else:
                self._json(404, {"error": "not found"})
        except Exception as exc:  # never let one bad request take the kiosk down
            sys.stderr.write(f"[error] {type(exc).__name__}: {exc}\n")
            self._json(500, {"error": f"{type(exc).__name__}"})


def make_server(port: int | None = None, force_mock: bool = False) -> tuple[ThreadingHTTPServer, App]:
    app = App(force_mock=force_mock)
    handler = type("BoundHandler", (Handler,), {"app": app})
    server = ThreadingHTTPServer(("127.0.0.1", port or app.settings.port), handler)
    server.daemon_threads = True
    return server, app


def main() -> None:
    force_mock = "--mock" in sys.argv
    server, app = make_server(force_mock=force_mock)
    host, port = server.server_address
    brain = f"live, {app.settings.model}" if app.mode == "live" else "scripted demo (no API key found in .env)"
    print(f"Sorty is running at http://localhost:{port}   brain: {brain}   station: {app.station['id']}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
