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
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from brain import Brain, get_settings, has_api_key, load_station  # noqa: E402
from brain.mock_brain import MockBrain  # noqa: E402
from brain import budget  # noqa: E402
from brain import guard as load_guard  # noqa: E402
from brain.persona import simulated_answer  # noqa: E402

KIOSK_DIR = ROOT / "kiosk"
SHOWCASE_DIR = ROOT / "showcase"
IMAGES_DIR = ROOT / "tests" / "images"
SCENARIOS_FILE = ROOT / "tests" / "scenarios.json"
MAX_BODY = 12 * 1024 * 1024

# The two AI setups the showcase can switch between while the server runs (POST /api/profile).
PROFILES = {
    "standard": {"label": "Standard", "detail": "Most careful: separate grease check on every second look",
                 "model": "claude-opus-5-5", "prearm_specialist": True},
    "fast": {"label": "Faster", "detail": "Faster and about half the cost: grease check only when unsure",
             "model": "claude-sonnet-5-5", "prearm_specialist": False},
}

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
        # Name the AI setup the environment asked for. The settings stay as they are until a setup is chosen.
        fast = PROFILES["fast"]
        if self.settings.model == fast["model"] and self.settings.prearm_specialist == fast["prearm_specialist"]:
            self.profile = "fast"
        else:
            self.profile = "standard" if self.settings.model == PROFILES["standard"]["model"] else "custom"
        self.station = load_station(self.settings.station_id)
        self.scenarios = load_scenarios()
        self._forced_mock = force_mock or os.environ.get("SORTY_MODE", "").lower() == "mock"
        self._chosen_mock = False       # practice mode switched on by hand (POST /api/mode): holds until switched off
        self._budget_used = False       # practice mode because the AI budget ran out: holds until the server restarts
        self._pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="sorty")
        self._guard = None              # the instant alert, built on first use
        want_mock = self._forced_mock or not self._has_key()
        if want_mock:
            self.brain = MockBrain(self.settings, self.station, self.scenarios)
        else:
            self.brain = self._live_brain()
        self.mode = self.brain.mode

    def _has_key(self) -> bool:
        """Is there a key for the AI service this setup uses? (Claude, or Gemini with the LangGraph brain.)"""
        if self.settings.orchestrator == "langgraph":
            try:
                from brain import providers
                if providers.resolve(self.settings)[0] == "google":
                    return providers.has_gemini_key()
            except Exception:
                pass
        return has_api_key()

    def _live_brain(self):
        """The careful brain: the classic loop, or the LangGraph one (SORTY_ORCHESTRATOR=langgraph)."""
        if self.settings.orchestrator == "langgraph":
            try:
                from brain.graph_brain import GraphBrain
                return GraphBrain(self.settings, station=self.station)
            except Exception as exc:    # packages missing or a setup problem: the classic loop does the same job
                print(f"LangGraph brain unavailable ({type(exc).__name__}: {exc}); using the classic loop.", flush=True)
        return Brain(self.settings, station=self.station)

    def guard(self):
        """The instant alert model, or None when it is switched off or cannot run (no Claude key)."""
        if not self.settings.guard or self.mode != "live" or not has_api_key():
            return None
        if self._guard is None:
            try:
                self._guard = load_guard.LoadGuard(self.settings, self.station)
            except Exception as exc:
                print(f"Instant alert unavailable ({type(exc).__name__}).", flush=True)
                self.settings.guard = False
                return None
        return self._guard

    def start_session(self, image: str, lang: str = "en", demo: str | None = None) -> dict:
        """The station has activated. Two models start on the same frame at the same time: the fast
        guard (is this one of the few things that wreck a whole load?) and the careful brain. If the
        guard is sure, its alert is the answer and nobody waits for the careful brain."""
        brain = self.brain
        if not self.settings.guard:
            return brain.start(image, lang, demo)
        if self.mode != "live":
            # Practice mode: scenarios marked as load-wreckers show the same alert, scripted.
            sc = self.scenarios.get(demo or "") or {}
            if sc.get("guard") in load_guard.WRECKERS:
                time.sleep(0.6)
                return load_guard.alert_turn(self.station, sc["guard"], sc.get("guard_item", ""), lang, 600, "scripted")
            return brain.start(image, lang, demo)
        guard = self.guard()
        if guard is None:
            return brain.start(image, lang, demo)

        careful = self._pool.submit(brain.start, image, lang, demo)
        fast = self._pool.submit(guard.look, image)
        done, _ = wait([fast, careful], timeout=self.settings.guard_wait_s, return_when=FIRST_COMPLETED)
        look = fast.result() if fast in done else None
        if look and look.get("alert"):
            careful.add_done_callback(lambda f: self._forget(brain, f))     # the careful pass is no longer needed
            return load_guard.alert_turn(self.station, look["category"], look["item"], lang, look["ms"],
                                         f"fast check, {guard.model}")
        turn = careful.result()
        if look and "error" not in look:
            note = {"t_ms": look["ms"], "kind": "guard",
                    "text": f"Fast check ({guard.model}, {look['ms'] / 1000:.1f} s): nothing that wrecks a load"}
            sess = getattr(brain, "sessions", {}).get(turn.get("session_id"))
            if sess is not None and isinstance(getattr(sess, "trace", None), list):
                sess.trace.insert(min(1, len(sess.trace)), note)            # later turns keep the line too
            if isinstance(turn.get("trace"), list):
                turn["trace"].insert(min(1, len(turn["trace"])), note)
            turn["guard"] = {"clear": True, "ms": look["ms"]}
        return turn

    @staticmethod
    def _forget(brain, finished) -> None:
        try:
            brain.end(finished.result().get("session_id"))
        except Exception:
            pass

    def guard_look(self, image: str) -> dict:
        """One fast look on its own (POST /api/guard): for measuring the alert, or an always-on watch."""
        guard = self.guard()
        if guard is None:
            return {"alert": False, "error": "instant alert is not running"}
        look = guard.look(image)
        look["model"] = guard.model
        return look

    def go_live_if_possible(self) -> None:
        """Practice mode ends by itself once an API key has been put in .env: no restart needed."""
        if self.mode == "live" or self._forced_mock or self._chosen_mock or not self._has_key():
            return
        self.brain = self._live_brain()
        self.mode = self.brain.mode
        print(f"API key found: switched to the live brain ({self.settings.model}).", flush=True)

    def stop_if_budget_used(self) -> None:
        """Once the AI budget is used up, stop calling the AI and run in practice mode."""
        if self.mode == "live" and budget.exhausted():
            self.brain = MockBrain(self.settings, self.station, self.scenarios)
            self.mode = self.brain.mode
            self._forced_mock = True
            self._budget_used = True
            print(f"AI budget used up (about ${budget.spent_usd():.2f}): back to practice mode.", flush=True)

    def why_practice(self) -> str | None:
        """Why the answers are scripted right now (None while the AI is connected), so the page can explain itself."""
        if self.mode == "live":
            return None
        if self._budget_used:
            return "budget"
        if self._forced_mock:
            return "forced"
        return "chosen" if self._chosen_mock else "no_key"

    def set_mode(self, name: str) -> dict:
        """Switch practice mode on or off by hand and return the new config: for when the connection fails.
        "practice" holds until "live" is asked for. "live" only happens with a key and budget left, and never
        after a --mock start or a used-up budget: those last until the server is restarted."""
        if name not in ("practice", "live"):
            raise ValueError("mode must be one of: practice, live")
        self._chosen_mock = name == "practice"
        if self._chosen_mock and self.mode == "live":
            self.brain = MockBrain(self.settings, self.station, self.scenarios)
            self.mode = self.brain.mode
            print("Practice mode switched on by hand: scripted answers, no AI calls.", flush=True)
        return self.config()        # switching back to the AI, when that is possible, happens in here

    def config(self) -> dict:
        self.go_live_if_possible()
        self.stop_if_budget_used()
        s = self.settings
        return {
            "assistant_name": s.assistant_name,
            "mode": self.mode,
            "model": getattr(self.brain, "model_id", s.model) if self.mode == "live" else None,
            "orchestrator": s.orchestrator if self.mode == "live" else None,
            "guard": {"on": bool(s.guard), "model": s.guard_model if self.mode == "live" else None},
            "lang_default": "en",
            "languages": s.languages,
            "station": {"id": self.station["id"], "name": self.station.get("name", ""), "bins": self.station["bins"]},
            "timeouts": {"answer_s": s.answer_timeout_s, "show_s": s.show_timeout_s, "verdict_hold_s": s.verdict_hold_s},
            "budget": budget.status(),
            "profile": {"name": self.profile, "options": [
                {"name": name, "label": p["label"], "detail": p["detail"], "model": p["model"]}
                for name, p in PROFILES.items()]},
            "why_practice": self.why_practice(),
        }

    def set_profile(self, name: str) -> dict:
        """Switch to one of the named AI setups and return the new config. The live brain reads both
        settings on every AI call, so no restart is needed; in practice mode the choice waits for the AI."""
        if not isinstance(name, str) or name not in PROFILES:
            raise ValueError("profile must be one of: " + ", ".join(PROFILES))
        setup = PROFILES[name]
        self.settings.model = setup["model"]
        self.settings.prearm_specialist = setup["prearm_specialist"]
        self.profile = name
        return self.config()

    def notify(self, turn: dict) -> None:
        """Tell the bin hardware about a verdict (for example to light the LED of
        the right bin). Set SORTY_NOTIFY_URL to the controller's address; the
        verdict is POSTed there as JSON. Never blocks or breaks the kiosk."""
        import os
        url = os.environ.get("SORTY_NOTIFY_URL")
        if not url or turn.get("type") != "verdict":
            return
        payload = json.dumps({"primary_bin": turn["verdict"]["primary_bin"], "steps": turn["verdict"]["steps"]}).encode("utf-8")

        def post() -> None:
            try:
                import urllib.request
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=2).close()
            except Exception:
                pass

        threading.Thread(target=post, daemon=True).start()

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
        if hasattr(self.brain, "simulated_answer"):          # the LangGraph brain answers with its own model
            return self.brain.simulated_answer(person.get("facts", ""), question, sc.get("lang", "en"))
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
        elif path == "/showcase":
            self.send_response(302)
            self.send_header("Location", "/showcase/")
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif path.startswith("/showcase/"):
            self._static(SHOWCASE_DIR, path[len("/showcase/"):])
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
                turn = self.app.start_session(body["image"], str(body.get("lang") or "en"), body.get("demo_scenario") or None)
                self.app.notify(turn)
                self._json(200, turn)
            elif path == "/api/guard":
                if not body.get("image"):
                    self._json(400, {"error": "image is required"})
                    return
                self._json(200, self.app.guard_look(body["image"]))
            elif len(parts) == 4 and parts[:2] == ["api", "session"] and parts[3] == "reply":
                turn = self.app.brain.reply(parts[2], body)
                self.app.notify(turn)
                self._json(200, turn)
            elif len(parts) == 4 and parts[:2] == ["api", "session"] and parts[3] == "end":
                self.app.brain.end(parts[2])
                self._json(200, {})
            elif path == "/api/demo/answer":
                text = self.app.demo_answer(str(body.get("scenario_id", "")), str(body.get("question", "")))
                self._json(200, {"text": text})
            elif path == "/api/profile":
                try:
                    cfg = self.app.set_profile(body.get("profile"))
                except ValueError as exc:
                    self._json(400, {"error": str(exc)})
                    return
                self._json(200, cfg)
            elif path == "/api/mode":
                try:
                    cfg = self.app.set_mode(body.get("mode"))
                except ValueError as exc:
                    self._json(400, {"error": str(exc)})
                    return
                self._json(200, cfg)
            else:
                self._json(404, {"error": "not found"})
        except Exception as exc:  # never let one bad request take the kiosk down
            sys.stderr.write(f"[error] {type(exc).__name__}: {exc}\n")
            self._json(500, {"error": f"{type(exc).__name__}"})


def make_server(port: int | None = None, force_mock: bool = False) -> tuple[ThreadingHTTPServer, App]:
    app = App(force_mock=force_mock)
    handler = type("BoundHandler", (Handler,), {"app": app})
    server = ThreadingHTTPServer(("127.0.0.1", app.settings.port if port is None else port), handler)
    server.daemon_threads = True
    return server, app


def main() -> None:
    force_mock = "--mock" in sys.argv
    server, app = make_server(force_mock=force_mock)
    host, port = server.server_address
    brain = f"live, {app.settings.model}" if app.mode == "live" else "scripted demo (no API key found in .env)"
    print(f"Sorty is running at http://localhost:{port}   brain: {brain}   station: {app.station['id']}", flush=True)
    print(f"Virtual prototype (showcase): http://localhost:{port}/showcase/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
