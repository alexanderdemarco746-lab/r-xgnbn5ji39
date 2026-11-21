"""A scripted stand-in for the brain, used when no API key is configured.

It returns turns in exactly the same shape as the real brain, following the
'mock' script of a demo scenario (or a small rotation of canned flows for a
live camera), so the kiosk can be shown and developed without any AI calls.
It does not look at the image.
"""
from __future__ import annotations

import secrets
import threading
import time

from .agent import Brain, Session
from .config import Settings, get_settings, load_station

_ROTATION = [
    {"title": "Pizza box",
     "show": {"action": "open_show_inside", "say": "Open the box and show me inside.", "because": "I can't see the inside."},
     "verdict": {"items": [{"item": "Greasy pizza box", "bin": "compost", "prep": ""}], "reason": "Grease spoils paper recycling."}},
    {"title": "Soda can",
     "ask": {"question": "Is there liquid inside?", "because": "I can't see inside the can.", "answer": "Yes, a little."},
     "verdict": {"items": [{"item": "Soda can", "bin": "recycle", "prep": "Pour out the soda"}], "reason": "Liquid spoils the recycling."}},
    {"title": "Chip bag",
     "verdict": {"items": [{"item": "Chip bag", "bin": "landfill", "prep": ""}], "reason": "Shiny film is not foil."}},
    {"title": "Batteries",
     "verdict": {"items": [{"item": "Batteries", "bin": "special", "prep": "", "special_dest": "the battery drop-off box"}],
                 "reason": "Batteries can start fires in the truck."}},
]

_DEFAULT_SAY = {
    "open_show_inside": "Open it and show me inside.",
    "flip_over": "Turn it around.",
    "show_bottom": "Show me the bottom.",
    "show_label": "Show me the label.",
    "hold_closer": "Hold it a little closer.",
    "one_at_a_time": "Show me one thing at a time.",
    "hold_still": "Hold it still for a moment.",
}


class MockBrain(Brain):
    mode = "mock"

    def __init__(self, settings: Settings | None = None, station: dict | None = None,
                 scenarios: dict | None = None, delay_s: float = 0.7) -> None:
        # Deliberately does not call Brain.__init__: no API client is created.
        self.s = settings or get_settings()
        self.station = station or load_station(self.s.station_id)
        self.bins = {b["id"]: b for b in self.station["bins"]}
        self.sessions: dict[str, Session] = {}
        self._lock = threading.Lock()
        self.scenarios = scenarios or {}
        self.delay_s = delay_s
        self._scripts: dict[str, list] = {}
        self._rotation = 0

    def _bin_or_fallback(self, bin_id: str) -> str:
        if bin_id in self.bins or bin_id in ("special", "not_trash"):
            return bin_id
        return "landfill" if "landfill" in self.bins else next(iter(self.bins))

    def _script(self, scenario: dict | None) -> list:
        if scenario is None:
            mock = _ROTATION[self._rotation % len(_ROTATION)]
            self._rotation += 1
            title = mock["title"]
        else:
            # Only the part before the comma: "Soda can, half full" must not reveal the hidden fact.
            title = scenario.get("title", "Item").split(",")[0].strip()
            mock = dict(scenario.get("mock") or {})
            if not mock:
                extra_views = [k for k in scenario.get("frames", {}) if k != "initial"]
                expect = scenario.get("expect", {})
                if extra_views:
                    mock["show"] = {"action": extra_views[0], "say": _DEFAULT_SAY.get(extra_views[0], "Show me again."), "because": ""}
                elif expect.get("needs") == "ask":
                    mock["ask"] = {"question": "Is it empty?", "because": "I can't see inside.", "answer": "Yes."}
                first_bin = (expect.get("bins") or ["landfill"])[0]
                mock["verdict"] = {"items": [{"item": title, "bin": first_bin, "prep": ""}], "reason": scenario.get("why", "")[:60]}
        steps = []
        if "show" in mock:
            steps.append(("show", {"item_seen": title, "then_check": "none", **mock["show"]}))
        if "ask" in mock:
            steps.append(("ask", {"kind": "yes_no", "options": [], "item_seen": title, "fact": "", **mock["ask"]}))
        verdict = dict(mock["verdict"])
        verdict["items"] = [{"special_dest": "", **it, "bin": self._bin_or_fallback(it["bin"])} for it in verdict["items"]]
        steps.append(("verdict", {"confidence": "high", **verdict}))
        return steps

    def _play(self, sess: Session, t0: float) -> dict:
        time.sleep(self.delay_s)
        steps = self._scripts[sess.id]
        kind, args = steps.pop(0)
        if kind == "show":
            sess.person_turns += 1
            sess.pending = {"name": "request_new_view"}
            return self._show_turn(sess, t0, args)
        if kind == "ask":
            sess.person_turns += 1
            sess.pending = {"name": "ask_person"}
            return self._ask_turn(sess, t0, args)
        return self._verdict_turn(sess, t0, args) or self._error_turn(sess, t0, "empty mock verdict")

    def start(self, image_b64: str, lang: str = "en", demo_scenario: str | None = None,
              max_person_turns: int | None = None) -> dict:
        t0 = time.monotonic()
        sess = Session(id="s_" + secrets.token_hex(4), lang=lang if lang in self.s.languages else "en",
                       max_person_turns=self.s.max_person_turns, demo_scenario=demo_scenario)
        with self._lock:
            self._purge()
            self.sessions[sess.id] = sess
            self._scripts[sess.id] = self._script(self.scenarios.get(demo_scenario) if demo_scenario else None)
        sess.note("frame", "Item presented to the camera (scripted demo, no AI call)")
        return self._play(sess, t0)

    def reply(self, session_id: str, payload: dict) -> dict:
        t0 = time.monotonic()
        sess = self.sessions.get(session_id)
        if sess is None or sess.finished or not sess.pending:
            ghost = sess or Session(id=session_id, lang="en", max_person_turns=0)
            return self._error_turn(ghost, t0, "session is not waiting for a reply")
        sess.pending = None
        kind = (payload or {}).get("type")
        if kind == "answer":
            sess.note("answer", f'Person: "{str(payload.get("text", ""))[:80]}"')
        elif kind == "frame":
            sess.note("frame", "New view received")
        else:
            sess.note("answer", "No response from the person")
        return self._play(sess, t0)

    def end(self, session_id: str) -> None:
        with self._lock:
            self.sessions.pop(session_id, None)
            self._scripts.pop(session_id, None)

    def mock_answer(self, demo_scenario: str) -> str:
        scenario = self.scenarios.get(demo_scenario) or {}
        return ((scenario.get("mock") or {}).get("ask") or {}).get("answer", "Yes.")
