"""Sorty's decision loop.

One interaction = one Session. The kiosk sends a camera frame; the brain keeps
calling Claude until it either needs the person (a question, or "show me
again") or has a verdict. Specialist checks are resolved here without the
person noticing. Each call to start()/reply() returns one Turn dict, which is
exactly what the kiosk renders and speaks.

Guardrails enforced in code, not left to the model:
  - a hard budget of requests to the person (people leave after ~10 seconds)
  - every interaction ends with an answer, even when the model or network fails
  - only bins that exist on this station can be named
  - nothing the person says is treated as an instruction
"""
from __future__ import annotations

import io
import json
import secrets
import threading
import time
from dataclasses import dataclass, field

import anthropic
from PIL import Image

from . import budget, phrases, prompts
from .config import Settings, get_settings, load_station
from .imaging import BadImage, decode_frame, main_view, to_block
from .llm import LLM
from .specialists import build_specialists, run_checks, summarize
from .tools import SPECIALIST_CHECKS, VIEW_ACTIONS, build_tools

SESSION_TTL_S = 300


@dataclass
class Session:
    id: str
    lang: str
    max_person_turns: int
    demo_scenario: str | None = None
    started: float = field(default_factory=time.monotonic)
    messages: list = field(default_factory=list)
    pending: dict | None = None          # the tool call waiting on the person
    person_turns: int = 0
    specialist_calls: int = 0
    model_calls: int = 0
    nudges: int = 0
    turn_no: int = 0
    finished: bool = False
    last_frame: bytes | None = None
    last_thumb: bytes | None = None
    trace: list = field(default_factory=list)
    log: list = field(default_factory=list)   # structured record for tests
    lock: threading.Lock = field(default_factory=threading.Lock)

    def note(self, kind: str, text: str) -> None:
        self.trace.append({"t_ms": int((time.monotonic() - self.started) * 1000), "kind": kind, "text": text})


def _thumb(raw: bytes) -> bytes:
    img = Image.open(io.BytesIO(raw)).convert("RGB").resize((48, 48))
    return img.tobytes()


def _looks_unchanged(a: bytes | None, b: bytes | None) -> bool:
    """Cheap check that a new frame is practically the previous one.

    Deliberately conservative: an item turned over in the hand changes only a
    small part of the picture, and that must still count as a new view. So a
    frame is "unchanged" only when almost no pixel moved by more than sensor
    noise.
    """
    if not a or not b or len(a) != len(b):
        return False
    diffs = [abs(x - y) for x, y in zip(a, b)]
    changed = sum(1 for d in diffs if d > 30) / len(diffs)
    return changed < 0.005 and sum(diffs) / len(diffs) < 3.0


class Brain:
    mode = "live"

    def __init__(self, settings: Settings | None = None, llm: LLM | None = None,
                 specialists: dict | None = None, station: dict | None = None) -> None:
        self.s = settings or get_settings()
        self.station = station or load_station(self.s.station_id)
        self.bins = {b["id"]: b for b in self.station["bins"]}
        self.llm = llm or LLM(self.s)
        self.tools = build_tools(self.station)
        self.specialists = specialists if specialists is not None else build_specialists(self.llm, self.s)
        self.sessions: dict[str, Session] = {}
        self._lock = threading.Lock()
        self._system: dict[str, str] = {}

    # ------------------------------------------------------------------ API
    def start(self, image_b64: str, lang: str = "en", demo_scenario: str | None = None,
              max_person_turns: int | None = None) -> dict:
        lang = lang if lang in self.s.languages else "en"
        sess = Session(
            id="s_" + secrets.token_hex(4), lang=lang, demo_scenario=demo_scenario,
            max_person_turns=self.s.max_person_turns if max_person_turns is None else max_person_turns,
        )
        t0 = time.monotonic()
        with self._lock:
            self._purge()
            self.sessions[sess.id] = sess
        with sess.lock:
            try:
                frame = decode_frame(image_b64)
                view = main_view(frame, self.s.main_image_px)
            except BadImage as exc:
                return self._error_turn(sess, t0, f"bad image: {exc}")
            sess.last_frame, sess.last_thumb = frame, _thumb(view)
            sess.messages.append({"role": "user", "content": [
                {"type": "text", "text": prompts.FIRST_FRAME_NOTE},
                to_block(view),
            ]})
            sess.note("frame", "Item presented to the camera")
            return self._advance_safely(sess, t0)

    def reply(self, session_id: str, payload: dict) -> dict:
        t0 = time.monotonic()
        sess = self.sessions.get(session_id)
        if sess is None:
            ghost = Session(id=session_id, lang="en", max_person_turns=0)
            return self._error_turn(ghost, t0, "unknown or expired session")
        with sess.lock:
            if sess.finished or not sess.pending:
                return self._error_turn(sess, t0, "session is not waiting for a reply")
            pending, sess.pending = sess.pending, None
            try:
                blocks = self._reply_blocks(sess, pending, payload or {})
            except BadImage as exc:
                return self._error_turn(sess, t0, f"bad image: {exc}")
            results = [{"type": "tool_result", "tool_use_id": pending["id"], "content": blocks}]
            results += [self._ignored(extra_id) for extra_id in pending.get("extra", [])]
            sess.messages.append({"role": "user", "content": results})
            return self._advance_safely(sess, t0)

    def end(self, session_id: str) -> None:
        with self._lock:
            self.sessions.pop(session_id, None)

    def session_log(self, session_id: str) -> dict | None:
        """Structured record of an interaction, for the scenario tests."""
        sess = self.sessions.get(session_id)
        if sess is None:
            return None
        return {"person_turns": sess.person_turns, "specialist_calls": sess.specialist_calls,
                "model_calls": sess.model_calls, "events": list(sess.log), "trace": list(sess.trace)}

    # ------------------------------------------------------------ internals
    def _purge(self) -> None:
        now = time.monotonic()
        for sid in [k for k, v in self.sessions.items() if now - v.started > SESSION_TTL_S]:
            self.sessions.pop(sid, None)

    def _system_prompt(self, lang: str) -> str:
        if lang not in self._system:
            self._system[lang] = prompts.build_system_prompt(self.station, lang, self.s.max_person_turns)
        return self._system[lang]

    def _call_model(self, sess: Session):
        return self.llm.create(
            model=self.s.model,
            effort=self.s.effort,
            system=[{"type": "text", "text": self._system_prompt(sess.lang), "cache_control": {"type": "ephemeral"}}],
            tools=self.tools,
            tool_choice={"type": "auto", "disable_parallel_tool_use": True},
            messages=sess.messages,
            cache_control={"type": "ephemeral"},
        )

    @staticmethod
    def _ignored(tool_use_id: str) -> dict:
        return {"type": "tool_result", "tool_use_id": tool_use_id, "is_error": True,
                "content": "Ignored: only one tool call per turn is processed."}

    def _reply_blocks(self, sess: Session, pending: dict, payload: dict) -> list:
        kind = payload.get("type")
        asked_view = pending["name"] == "request_new_view"
        if kind == "answer":
            text = str(payload.get("text", "")).strip()[:300] or "(silence)"
            text = {"unsure": "not sure"}.get(text.lower(), text)
            sess.note("answer", f'Person: "{text}"')
            sess.log.append({"event": "answer", "text": text})
            lead = "Instead of showing a new view, the person said" if asked_view else "The person answered"
            return [{"type": "text", "text": f'{lead}: "{text}"'}]
        if kind == "frame":
            frame = decode_frame(payload.get("image", ""))
            view = main_view(frame, self.s.main_image_px)
            thumb = _thumb(view)
            unchanged = _looks_unchanged(sess.last_thumb, thumb)
            sess.last_frame, sess.last_thumb = frame, thumb
            lead = "New camera frame after your request." if asked_view else \
                "The person did not answer in words. Here is the current camera frame instead."
            if unchanged:
                lead += (" Note: it is practically identical to the previous frame. Check whether the "
                         "person actually did what you asked.")
            sess.note("frame", "New view received" + (" (looks unchanged)" if unchanged else ""))
            sess.log.append({"event": "frame", "unchanged": unchanged})
            blocks = [{"type": "text", "text": lead}, to_block(view)]
            check = pending["input"].get("then_check", "none") if asked_view and self.s.prearm_specialist else "none"
            if check in SPECIALIST_CHECKS and not unchanged and sess.specialist_calls < self.s.max_specialist_calls:
                focus = pending["input"].get("because", "") or pending["input"].get("say", "")
                results = self._run_specialists(sess, [check], focus)
                blocks.append({"type": "text", "text": "Specialist report on this new frame: " + json.dumps(results)})
            return blocks
        # timeout, or anything unrecognised
        what = "show a new view" if asked_view else "answer"
        sess.note("answer", "No response from the person")
        sess.log.append({"event": "timeout"})
        return [{"type": "text", "text": (
            f"No response: the person did not {what} in time. They may be in a hurry or may have "
            "walked away. Give your verdict now.")}]

    def _run_specialists(self, sess: Session, checks: list[str], focus: str) -> dict:
        if sess.last_frame is None:
            return {}
        sess.specialist_calls += 1
        results = run_checks(self.specialists, checks, sess.last_frame, focus)
        for name, result in results.items():
            sess.note("specialist", summarize(name, result))
            sess.log.append({"event": "specialist", "check": name, "result": result})
        return results

    def _advance_safely(self, sess: Session, t0: float) -> dict:
        try:
            return self._advance(sess, t0)
        except budget.BudgetExceeded as exc:
            return self._error_turn(sess, t0, str(exc))
        except anthropic.AuthenticationError:
            return self._error_turn(sess, t0, "the API key was rejected")
        except anthropic.PermissionDeniedError:
            return self._error_turn(sess, t0, "the API key lacks permission for this model")
        except anthropic.NotFoundError:
            return self._error_turn(sess, t0, f"model '{self.s.model}' was not found")
        except anthropic.RateLimitError:
            return self._error_turn(sess, t0, "rate limited by the API")
        except anthropic.BadRequestError as exc:
            return self._error_turn(sess, t0, f"request rejected: {exc.message}")
        except anthropic.APIStatusError as exc:
            return self._error_turn(sess, t0, f"API error {exc.status_code}")
        except anthropic.APIConnectionError:
            return self._error_turn(sess, t0, "no connection to the API")

    def _advance(self, sess: Session, t0: float) -> dict:
        while True:
            if sess.model_calls >= self.s.max_model_calls:
                return self._error_turn(sess, t0, "decision took too many steps")
            resp = self._call_model(sess)
            sess.model_calls += 1
            if resp.stop_reason in ("refusal", "max_tokens"):
                return self._error_turn(sess, t0, f"model stopped: {resp.stop_reason}")
            # Append the full content (thinking blocks included) unchanged: history is append-only.
            sess.messages.append({"role": "assistant", "content": resp.content})
            calls = [b for b in resp.content if b.type == "tool_use"]
            if not calls:
                if sess.nudges >= 2:
                    return self._error_turn(sess, t0, "model did not choose a move")
                sess.nudges += 1
                sess.messages.append({"role": "user", "content": prompts.NUDGE})
                continue
            call, extra = calls[0], calls[1:]
            name, args = call.name, dict(call.input or {})

            def answer_now(text: str, is_error: bool = False) -> None:
                result = {"type": "tool_result", "tool_use_id": call.id, "content": text}
                if is_error:
                    result["is_error"] = True
                sess.messages.append({"role": "user", "content": [result] + [self._ignored(e.id) for e in extra]})

            if name == "run_specialist":
                if sess.specialist_calls >= self.s.max_specialist_calls:
                    answer_now("No more specialist checks are available for this item. Decide with what you have.", True)
                    continue
                results = self._run_specialists(sess, list(args.get("checks") or []), str(args.get("focus", "")))
                answer_now(json.dumps(results) if results else "No such check.", not results)
                continue

            if name in ("request_new_view", "ask_person"):
                if sess.person_turns >= sess.max_person_turns:
                    sess.note("think", "Out of requests to the person: must decide now")
                    answer_now("You have used all your requests to the person for this item. Call give_verdict "
                               "now with the answer that is right whichever way the unknown fact turns out.", True)
                    continue
                sess.person_turns += 1
                sess.pending = {"id": call.id, "name": name, "input": args, "extra": [e.id for e in extra]}
                if name == "request_new_view":
                    return self._show_turn(sess, t0, args)
                return self._ask_turn(sess, t0, args)

            if name == "give_verdict":
                turn = self._verdict_turn(sess, t0, args)
                if turn is not None:
                    return turn
                answer_now("That verdict named no usable item. Call give_verdict again with at least one item.", True)
                continue

            if name == "nothing_to_sort":
                return self._no_item_turn(sess, t0, args)

            answer_now(f"Unknown tool '{name}'.", True)

    # ----------------------------------------------------------- the turns
    def _turn(self, sess: Session, t0: float, type_: str, say: str, display: dict, **extra) -> dict:
        sess.turn_no += 1
        turn = {
            "session_id": sess.id,
            "turn": sess.turn_no,
            "type": type_,
            "say": say,
            "display": {"headline": "", "sub": "", "item_label": "", "icon": "eye", **display},
            **extra,
            "trace": list(sess.trace),
            "timing_ms": int((time.monotonic() - t0) * 1000),
        }
        return turn

    def _show_turn(self, sess: Session, t0: float, args: dict) -> dict:
        action = args.get("action") if args.get("action") in VIEW_ACTIONS else "hold_closer"
        say = phrases.sentence(phrases.cap(str(args.get("say", "")))) or phrases.t(sess.lang)["no_item"]
        item = str(args.get("item_seen", "")).strip()
        sess.note("show", f'Sees "{item or "something"}". Needs another view ({action}): "{say}"')
        sess.log.append({"event": "show", "action": action, "say": say, "item_seen": item,
                         "then_check": args.get("then_check", "none")})
        headline = say.rstrip(".")
        for joiner in (" and ", " y ", ", "):                 # "Open the box and show me inside" -> "Open the box"
            if len(headline) > 22 and joiner in headline:
                headline = headline.split(joiner)[0]
                break
        return self._turn(
            sess, t0, "show", say,
            {"headline": headline, "sub": str(args.get("because", "")).strip(),
             "item_label": item, "icon": phrases.ACTION_ICONS.get(action, "eye")},
            show={"action": action, "hint": say.rstrip(".")},
        )

    def _ask_turn(self, sess: Session, t0: float, args: dict) -> dict:
        tr = phrases.t(sess.lang)
        question = phrases.cap(str(args.get("question", "")).strip())
        if question and question[-1] not in "?!.":
            question += "?"
        item = str(args.get("item_seen", "")).strip()
        kind = "choice" if args.get("kind") == "choice" and args.get("options") else "yes_no"
        if kind == "choice":
            options = [{"id": str(o).strip(), "label": phrases.cap(str(o))} for o in list(args["options"])[:3] if str(o).strip()]
        else:
            options = [{"id": "yes", "label": tr["yes"]}, {"id": "no", "label": tr["no"]}]
        options.append({"id": "unsure", "label": tr["unsure"]})
        sess.note("ask", f'Sees "{item or "something"}". Camera cannot tell ({args.get("fact", "?")}): asks "{question}"')
        sess.log.append({"event": "ask", "question": question, "fact": args.get("fact", ""), "item_seen": item})
        return self._turn(
            sess, t0, "ask", question,
            {"headline": question, "sub": str(args.get("because", "")).strip(), "item_label": item, "icon": "question"},
            ask={"kind": kind, "options": options},
        )

    def _no_item_turn(self, sess: Session, t0: float, args: dict) -> dict:
        sess.finished = True
        say = phrases.sentence(str(args.get("say", "")).strip()) or phrases.t(sess.lang)["no_item"]
        sess.note("look", f'Nothing to sort: {args.get("what_i_see", "")}')
        sess.log.append({"event": "no_item", "what_i_see": args.get("what_i_see", "")})
        return self._turn(sess, t0, "no_item", say, {"headline": say.rstrip("."), "icon": "eye"})

    def _verdict_turn(self, sess: Session, t0: float, args: dict) -> dict | None:
        tr = phrases.t(sess.lang)
        items = []
        for raw in list(args.get("items") or [])[:2]:
            bin_id = raw.get("bin")
            if bin_id not in self.bins and bin_id not in ("special", "not_trash"):
                continue
            items.append({
                "item": phrases.cap(str(raw.get("item", "")).strip()) or "Item",
                "bin": bin_id,
                "prep": phrases.clean_prep(str(raw.get("prep", ""))),
                "dest": str(raw.get("special_dest", "")).strip().rstrip("."),
            })
        if not items:
            return None

        steps, spoken = [], []
        many = len(items) > 1
        for it in items:
            if it["bin"] == "special":
                dest = it["dest"] or tr["default_dest"]
                steps.append({"kind": "special", "item": it["item"], "text": tr["special_headline"], "dest": phrases.cap(dest)})
                spoken.append(tr["special"].format(dest=dest))
                continue
            if it["bin"] == "not_trash":
                steps.append({"kind": "keep", "item": it["item"], "text": tr["keep"].rstrip(".")})
                spoken.append(tr["keep"])
                continue
            cfg = self.bins[it["bin"]]
            phrase = phrases.bin_phrase(cfg, sess.lang)
            if it["prep"]:
                steps.append({"kind": "prep", "text": phrases.cap(it["prep"])})
            steps.append({"kind": "bin", "item": it["item"], "bin": it["bin"],
                          "position": cfg["position"], "text": phrases.cap(phrase)})
            if many:
                lead = phrases.sentence(phrases.cap(it["prep"])) + " " if it["prep"] else ""
                spoken.append(lead + tr["item_bin"].format(item=it["item"], bin=phrase))
            elif it["prep"]:
                spoken.append(tr["first_then"].format(prep=phrases.lower_first(it["prep"]), bin=phrase))
            else:
                spoken.append(phrases.cap(tr["single"].format(bin=phrase)))

        reason = phrases.sentence(phrases.cap(str(args.get("reason", "")).strip()))
        say = " ".join(spoken)
        if reason and len((say + " " + reason).split()) <= 26:
            say += " " + reason
        primary = items[0]["bin"]
        if primary != "not_trash":
            say += " " + tr["thanks"]
        confidence = args.get("confidence") if args.get("confidence") in ("high", "medium", "low") else "medium"
        special_dest = next((s["dest"] for s in steps if s["kind"] == "special"), None)

        sess.finished = True
        label = ", ".join(i["item"] for i in items)
        where = " + ".join(i["bin"] for i in items)
        sess.note("verdict", f"{label} -> {where}. {reason}".strip())
        sess.log.append({"event": "verdict", "items": items, "reason": reason, "confidence": confidence})
        first_text = next((s["text"] for s in steps if s["kind"] != "prep"), steps[0]["text"])
        return self._turn(
            sess, t0, "verdict", say.strip(),
            {"headline": first_text, "sub": reason, "item_label": label,
             "icon": "warning" if primary == "special" else "eye"},
            verdict={"primary_bin": primary, "steps": steps, "reason": reason,
                     "special_dest": special_dest, "confidence": confidence},
        )

    def _error_turn(self, sess: Session, t0: float, why: str) -> dict:
        """Something failed. The person still gets guidance: read the bin labels."""
        tr = phrases.t(sess.lang)
        sess.finished = True
        sess.pending = None
        sess.note("think", f"Could not decide: {why}")
        sess.log.append({"event": "error", "why": why})
        return self._turn(sess, t0, "error", tr["error_say"],
                          {"headline": tr["error_headline"], "icon": "warning"}, error=why)
