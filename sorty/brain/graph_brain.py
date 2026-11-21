"""Sorty's decision loop as a LangGraph graph, running on Claude or Gemini.

Same job and same output as the classic loop in brain/agent.py (it reuses that
class's turn builders, so the kiosk sees identical Turn dicts), but the control
flow is an explicit graph:

    START -> think -+-> specialist -> think        (closer check on the current frame)
                    +-> person ----> think        (pause: ask the person, or wait for a new view)
                    +-> think                     (nudge, or a tool result that needs no pause)
                    +-> END                       (verdict, nothing to sort, or the safe error turn)

"person" pauses the graph with LangGraph's interrupt(); the kiosk's next request
resumes it with Command(resume=...). One checkpointer thread per session.

Guardrails live in the nodes, not in the model: the limit on requests to the
person, the cap on specialist checks and model calls, one tool per turn, and a
safe error turn whenever the provider or the network fails.
"""
from __future__ import annotations

import base64
import json
import operator
import secrets
import threading
import time
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from . import budget, prompts, providers
from .agent import Brain, Session, _looks_unchanged, _thumb
from .config import Settings, get_settings, load_station
from .imaging import BadImage, decode_frame, inspection_views, main_view
from .llm import Usage
from .tools import SPECIALIST_CHECKS, build_tools


class State(TypedDict, total=False):
    sid: str                                    # session id (bookkeeping lives in Brain.sessions)
    messages: Annotated[list, operator.add]     # the conversation with the model, append-only
    route: str                                  # where "think" or "person" sends the graph next
    turn: dict                                  # the Turn to hand to the kiosk
    pending: dict                               # the tool call that is waiting on the person or a check


def _image_block(jpeg: bytes) -> dict:
    """An image in the form both provider packages accept."""
    return {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.standard_b64encode(jpeg).decode("ascii")}}


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):] if "{" in text else text
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start:end + 1])


class ChatInspector:
    """A specialist check that works on any provider: the chat model answers in a fixed JSON shape."""

    def __init__(self, brain: "GraphBrain", name: str, system: str, schema: dict) -> None:
        self.brain, self.name, self.system, self.schema = brain, name, system, schema

    def run(self, frame: bytes, focus: str) -> dict:
        views = inspection_views(frame, self.brain.s.specialist_image_px)
        content = [_image_block(v) for v in views]
        content.append({"type": "text", "text": (
            f"Where to look and what to settle: {focus or 'the item being presented'}\n\n"
            "Answer with one JSON object and nothing else. It must have exactly these fields and allowed values:\n"
            + json.dumps(self.schema["properties"]))})
        try:
            msg = self.brain._invoke(self.brain._chat(False), [SystemMessage(content=self.system), HumanMessage(content=content)])
            return _parse_json(providers.text_of(msg))
        except (ValueError, json.JSONDecodeError):
            return {"error": "check returned unreadable output"}


class GraphBrain(Brain):
    mode = "live"
    orchestrator = "langgraph"

    def __init__(self, settings: Settings | None = None, station: dict | None = None,
                 specialists: dict | None = None, chat_factory=None) -> None:
        # Brain.__init__ is deliberately not called: it builds the Claude-only client.
        self.s = settings or get_settings()
        self.station = station or load_station(self.s.station_id)
        self.bins = {b["id"]: b for b in self.station["bins"]}
        self.tools = build_tools(self.station)
        self.sessions: dict[str, Session] = {}
        self._lock = threading.Lock()
        self._system: dict[str, str] = {}
        self._chat_factory = chat_factory            # tests hand in a scripted model
        self.guard_budget = chat_factory is None     # a scripted model spends nothing and is not tracked
        self.usage = Usage()
        self._models: dict[tuple, object] = {}
        self._t0: dict[str, float] = {}
        self._given_specialists = specialists
        self._built_specialists: dict[str, dict] = {}
        self._llm = None
        self.checkpointer = InMemorySaver()
        self.graph = self._build_graph()

    # ------------------------------------------------------------- the graph
    def _build_graph(self):
        g = StateGraph(State)
        g.add_node("think", self._think)
        g.add_node("specialist", self._specialist)
        g.add_node("person", self._person)
        g.add_edge(START, "think")
        routes = {"think": "think", "specialist": "specialist", "person": "person", "end": END}
        g.add_conditional_edges("think", lambda s: s.get("route", "end"), routes)
        g.add_edge("specialist", "think")
        g.add_conditional_edges("person", lambda s: s.get("route", "end"), {"think": "think", "end": END})
        return g.compile(checkpointer=self.checkpointer)

    # ------------------------------------------------------------ the models
    @property
    def provider(self) -> str:
        return providers.resolve(self.s)[0]

    @property
    def model_id(self) -> str:
        return providers.resolve(self.s)[1]

    def _chat(self, with_tools: bool):
        """The chat model for the current settings (rebuilt when the model or effort is switched at run time)."""
        provider, model_id = providers.resolve(self.s)
        key = (provider, model_id, with_tools, self.s.effort)
        if key not in self._models:
            base = self._chat_factory(self.s, model_id) if self._chat_factory else providers.make_chat_model(self.s, model_id)
            self._models[key] = providers.bind(base, self.tools, provider) if with_tools else base
        return self._models[key]

    def _invoke(self, runnable, messages: list):
        if self.guard_budget:
            budget.check()                             # raises BudgetExceeded once the spending limit is reached
        msg = runnable.invoke(messages)
        used = providers.usage_of(msg)
        self.usage.add(used)
        if self.guard_budget:
            budget.add(self.model_id, used)
        return msg

    def _system_message(self, lang: str) -> SystemMessage:
        text = self._system_prompt(lang)
        if self.provider == "anthropic":               # marks the instructions for Claude's prompt cache
            return SystemMessage(content=[{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}])
        return SystemMessage(content=text)

    @property
    def llm(self):
        """The classic Claude client: for the specialist checks on Claude, and for code that
        still asks the brain for one (the server's simulated demo person)."""
        if self._llm is None:
            from .llm import LLM
            self._llm = LLM(self.s)
            self._llm.usage = self.usage           # one running token total for brain and checks
        return self._llm

    @property
    def specialists(self) -> dict:
        if self._given_specialists is not None:
            return self._given_specialists
        provider = self.provider
        if provider not in self._built_specialists:
            if provider == "anthropic":
                from .specialists import build_specialists
                self._built_specialists[provider] = build_specialists(self.llm, self.s)
            else:
                self._built_specialists[provider] = {
                    "contamination": ChatInspector(self, "contamination", prompts.CONTAMINATION_SYSTEM, prompts.CONTAMINATION_SCHEMA),
                    "label": ChatInspector(self, "label", prompts.LABEL_SYSTEM, prompts.LABEL_SCHEMA),
                }
        return self._built_specialists[provider]

    def simulated_answer(self, facts: str, said: str, lang: str = "en") -> str:
        """The simulated person of the scenario tests, on whichever provider is in use."""
        language = prompts.LANGUAGE_NAMES.get(lang, "English")
        msg = self._invoke(self._chat(False), [
            SystemMessage(content=prompts.PERSONA_SYSTEM),
            HumanMessage(content=(f"Facts about you and what you are holding:\n{facts}\n\n"
                                  f'The assistant said: "{said}"\n\nReply in {language}, spoken words only.')),
        ])
        return providers.text_of(msg).strip().strip('"') or "not sure"

    def _why(self, exc: Exception) -> str:
        """A plain reason for the decision trace when a model call fails."""
        if isinstance(exc, budget.BudgetExceeded):
            return str(exc)
        try:
            import anthropic
            table = [
                (anthropic.AuthenticationError, "the API key was rejected"),
                (anthropic.PermissionDeniedError, "the API key lacks permission for this model"),
                (anthropic.NotFoundError, f"model '{self.model_id}' was not found"),
                (anthropic.RateLimitError, "rate limited by the API"),
                (anthropic.APIConnectionError, "no connection to the API"),
            ]
            for cls, why in table:
                if isinstance(exc, cls):
                    return why
            if isinstance(exc, anthropic.BadRequestError):
                return f"request rejected: {exc.message}"
            if isinstance(exc, anthropic.APIStatusError):
                return f"API error {exc.status_code}"
        except ImportError:
            pass
        name, text = type(exc).__name__, str(exc).lower()
        if "429" in text or "resource" in name.lower() and "exhaust" in name.lower() or "rate" in text and "limit" in text or "quota" in text:
            return "rate limited by the API"
        if "api key" in text or "api_key" in text or "unauthenticated" in text or "permission" in text:
            return "the API key was rejected"
        if "not found" in text and "model" in text:
            return f"model '{self.model_id}' was not found"
        if "connect" in name.lower() or "timeout" in name.lower() or "connection" in text:
            return "no connection to the API"
        return f"AI service error ({name})"

    # -------------------------------------------------------------- the nodes
    def _think(self, state: State) -> dict:
        """One model call: look at the conversation so far and pick exactly one move."""
        sess = self.sessions[state["sid"]]
        t0 = self._t0.get(sess.id, time.monotonic())
        if sess.model_calls >= self.s.max_model_calls:
            return {"route": "end", "turn": self._error_turn(sess, t0, "decision took too many steps")}
        try:
            msg = self._invoke(self._chat(True), [self._system_message(sess.lang)] + list(state.get("messages", [])))
        except Exception as exc:                        # provider or network failure: the person still gets guidance
            return {"route": "end", "turn": self._error_turn(sess, t0, self._why(exc))}
        sess.model_calls += 1
        if providers.stop_reason(msg) in ("refusal", "max_tokens"):
            return {"route": "end", "turn": self._error_turn(sess, t0, f"model stopped: {providers.stop_reason(msg)}")}

        calls = list(getattr(msg, "tool_calls", None) or [])
        if not calls:                                   # plain text: nobody hears that, so remind it once or twice
            if sess.nudges >= 2:
                return {"messages": [msg], "route": "end", "turn": self._error_turn(sess, t0, "model did not choose a move")}
            sess.nudges += 1
            return {"messages": [msg, HumanMessage(content=prompts.NUDGE)], "route": "think"}

        call, extra = calls[0], calls[1:]
        name, args = call["name"], dict(call.get("args") or {})
        call_id = call.get("id") or f"call_{sess.model_calls}"
        out = [msg] + [ToolMessage(content="Ignored: only one tool call per turn is processed.", name=e["name"],
                                   tool_call_id=e.get("id") or f"extra_{i}", status="error") for i, e in enumerate(extra)]

        def answer(text: str, error: bool = False) -> dict:
            out.append(ToolMessage(content=text, name=name, tool_call_id=call_id, status="error" if error else "success"))
            return {"messages": out, "route": "think"}

        if name == "run_specialist":
            if sess.specialist_calls >= self.s.max_specialist_calls:
                return answer("No more specialist checks are available for this item. Decide with what you have.", True)
            return {"messages": out, "route": "specialist", "pending": {"id": call_id, "name": name, "input": args}}

        if name in ("request_new_view", "ask_person"):
            if sess.person_turns >= sess.max_person_turns:
                sess.note("think", "Out of requests to the person: must decide now")
                return answer("You have used all your requests to the person for this item. Call give_verdict "
                              "now with the answer that is right whichever way the unknown fact turns out.", True)
            sess.person_turns += 1
            turn = self._show_turn(sess, t0, args) if name == "request_new_view" else self._ask_turn(sess, t0, args)
            return {"messages": out, "route": "person", "turn": turn, "pending": {"id": call_id, "name": name, "input": args}}

        if name == "give_verdict":
            turn = self._verdict_turn(sess, t0, args)
            if turn is None:
                return answer("That verdict named no usable item. Call give_verdict again with at least one item.", True)
            return {"messages": out, "route": "end", "turn": turn}

        if name == "nothing_to_sort":
            return {"messages": out, "route": "end", "turn": self._no_item_turn(sess, t0, args)}

        return answer(f"Unknown tool '{name}'.", True)

    def _specialist(self, state: State) -> dict:
        """Run the requested closer checks on the current frame and hand the report back to the model."""
        sess = self.sessions[state["sid"]]
        pending = state["pending"]
        args = pending["input"]
        results = self._run_specialists(sess, list(args.get("checks") or []), str(args.get("focus", "")))
        return {"messages": [ToolMessage(content=json.dumps(results) if results else "No such check.", name=pending["name"],
                                         tool_call_id=pending["id"], status="success" if results else "error")]}

    def _person(self, state: State) -> dict:
        """Pause until the kiosk brings the person's answer or a new camera frame."""
        payload = interrupt(state["turn"])              # nothing above this line: the node re-runs from here on resume
        sess = self.sessions[state["sid"]]
        t0 = self._t0.get(sess.id, time.monotonic())
        try:
            return {"messages": self._reply_messages(sess, state["pending"], payload or {}), "route": "think"}
        except BadImage as exc:
            return {"route": "end", "turn": self._error_turn(sess, t0, f"bad image: {exc}")}

    def _reply_messages(self, sess: Session, pending: dict, payload: dict) -> list:
        """What the model is told about the person's reply. Images travel in a human message, never in a tool message."""
        kind = payload.get("type")
        asked_view = pending["name"] == "request_new_view"

        def tool(text: str) -> ToolMessage:
            return ToolMessage(content=text, name=pending["name"], tool_call_id=pending["id"])

        if kind == "answer":
            text = str(payload.get("text", "")).strip()[:300] or "(silence)"
            text = {"unsure": "not sure"}.get(text.lower(), text)
            sess.note("answer", f'Person: "{text}"')
            sess.log.append({"event": "answer", "text": text})
            lead = "Instead of showing a new view, the person said" if asked_view else "The person answered"
            return [tool(f'{lead}: "{text}"')]
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
            parts = [{"type": "text", "text": "This is that camera frame."}, _image_block(view)]
            check = pending["input"].get("then_check", "none") if asked_view and self.s.prearm_specialist else "none"
            if check in SPECIALIST_CHECKS and not unchanged and sess.specialist_calls < self.s.max_specialist_calls:
                focus = pending["input"].get("because", "") or pending["input"].get("say", "")
                results = self._run_specialists(sess, [check], focus)
                parts.append({"type": "text", "text": "Specialist report on this new frame: " + json.dumps(results)})
            return [tool(lead), HumanMessage(content=parts)]
        what = "show a new view" if asked_view else "answer"
        sess.note("answer", "No response from the person")
        sess.log.append({"event": "timeout"})
        return [tool(f"No response: the person did not {what} in time. They may be in a hurry or may have "
                     "walked away. Give your verdict now.")]

    # ------------------------------------------------------------------ API
    def _run(self, sess: Session, t0: float, graph_input) -> dict:
        self._t0[sess.id] = t0
        try:
            result = self.graph.invoke(graph_input, {"configurable": {"thread_id": sess.id}})
        except Exception as exc:                        # never let a framework error reach the kiosk
            return self._error_turn(sess, t0, self._why(exc))
        waiting = result.get("__interrupt__")
        if waiting:
            sess.pending = {"waiting": True}
            return waiting[0].value
        turn = result.get("turn")
        return turn if turn else self._error_turn(sess, t0, "decision ended without an answer")

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
            sess.note("frame", "Item presented to the camera")
            first = HumanMessage(content=[{"type": "text", "text": prompts.FIRST_FRAME_NOTE}, _image_block(view)])
            return self._run(sess, t0, {"sid": sess.id, "messages": [first], "route": "think"})

    def reply(self, session_id: str, payload: dict) -> dict:
        t0 = time.monotonic()
        sess = self.sessions.get(session_id)
        if sess is None:
            ghost = Session(id=session_id, lang="en", max_person_turns=0)
            return self._error_turn(ghost, t0, "unknown or expired session")
        with sess.lock:
            if sess.finished or not sess.pending:
                return self._error_turn(sess, t0, "session is not waiting for a reply")
            sess.pending = None
            return self._run(sess, t0, Command(resume=payload or {}))

    def end(self, session_id: str) -> None:
        with self._lock:
            self.sessions.pop(session_id, None)
            self._t0.pop(session_id, None)
        try:
            self.checkpointer.delete_thread(session_id)
        except Exception:
            pass                                        # older checkpointers have no delete; memory is freed with the process
