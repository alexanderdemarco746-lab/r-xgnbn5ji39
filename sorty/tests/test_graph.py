"""Offline checks of the LangGraph orchestrator (brain/graph_brain.py).

No API key and no network: the chat model is a scripted fake. These verify the
graph's plumbing and guardrails, and that it hands the kiosk exactly the same
Turn dicts as the classic loop in brain/agent.py for the same model decisions.

    python -m tests.test_graph      (from the sorty folder)
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage  # noqa: E402

from brain import providers  # noqa: E402
from brain.config import Settings, load_station  # noqa: E402
from brain.graph_brain import GraphBrain  # noqa: E402
from brain.tools import build_tools  # noqa: E402
from tests.test_offline import ASK, SHOW, FakeSpecialist, frame, make_brain, response, tool, verdict  # noqa: E402

PASSED: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if not condition:
        raise AssertionError(f"{name} FAILED {detail}")
    PASSED.append(name)


class FakeChat:
    """Stands in for a LangChain chat model: returns scripted replies in order."""

    def __init__(self, script: list) -> None:
        self.script = list(script)
        self.requests: list[list] = []
        self.bound = None

    def bind_tools(self, tools, **kwargs):
        self.bound = (tools, kwargs)
        return self

    def invoke(self, messages, **kwargs):
        self.requests.append(list(messages))
        if not self.script:
            raise AssertionError("fake model ran out of scripted replies")
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def ai(name: str, args: dict, id_: str = "call_1") -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": id_, "type": "tool_call"}])


def make_graph(script: list, specialists: dict | None = None, station_id: str = "3bin", **overrides):
    settings = Settings(station_id=station_id, **overrides)
    fake = FakeChat(script)
    brain = GraphBrain(settings, station=load_station(station_id), specialists=specialists or {},
                       chat_factory=lambda s, model_id: fake)
    return brain, fake


def has_image(message) -> bool:
    return isinstance(message.content, list) and any(isinstance(b, dict) and b.get("type") == "image_url" for b in message.content)


def comparable(turn: dict) -> dict:
    """A Turn without the parts that legitimately differ between two runs."""
    t = copy.deepcopy(turn)
    t.pop("session_id", None)
    t.pop("timing_ms", None)
    for step in t.get("trace", []):
        step.pop("t_ms", None)
    return t


GREASE = {"surface_inspected": "inside of box", "surface_visible": "yes", "food_or_grease_present": "yes", "severity": "heavy",
          "coverage_percent": 45, "liquid_visible": "no", "evidence": "dark translucent patches", "confidence": "high"}
CAN_VERDICT = verdict([{"item": "soda can", "bin": "recycle", "prep": "Pour out the soda"}], "Liquid spoils the recycling")
BOX_VERDICT = verdict([{"item": "greasy pizza box", "bin": "compost"}], "Grease spoils paper recycling")


# ---------------------------------------------------------------------------
def test_ask_then_verdict():
    brain, fake = make_graph([ai("ask_person", ASK, "c_ask"), ai("give_verdict", CAN_VERDICT, "c_v")])
    turn = brain.start(frame(), "en")
    check("ask: graph pauses with an ask turn", turn["type"] == "ask" and turn["say"] == "Is there liquid inside?", str(turn))
    first = fake.requests[0]
    check("request: system prompt first, then a human message with the picture",
          isinstance(first[0], SystemMessage) and isinstance(first[1], HumanMessage) and has_image(first[1]))
    check("request: Claude's instructions are marked for the prompt cache",
          isinstance(first[0].content, list) and first[0].content[0].get("cache_control") == {"type": "ephemeral"})
    check("tools were bound with one call per turn", fake.bound and fake.bound[1].get("parallel_tool_calls") is False)
    turn2 = brain.reply(turn["session_id"], {"type": "answer", "text": "yes"})
    check("verdict after the answer", turn2["type"] == "verdict", str(turn2))
    check("verdict wording", turn2["say"] == "First, pour out the soda. Then: blue bin, on your left. Liquid spoils the recycling. Thank you!", turn2["say"])
    second = fake.requests[1]
    last = second[-1]
    check("the answer goes back as a tool message for the right call",
          isinstance(last, ToolMessage) and last.tool_call_id == "c_ask" and 'The person answered: "yes"' in last.content)
    check("history is append-only (first request is a prefix of the second)", second[:len(first)] == first)
    log = brain.session_log(turn["session_id"])
    check("one request to the person, two model calls", log["person_turns"] == 1 and log["model_calls"] == 2)
    check("trace: frame, ask, answer, verdict", [e["kind"] for e in turn2["trace"]] == ["frame", "ask", "answer", "verdict"])
    check("a finished session rejects further replies", brain.reply(turn["session_id"], {"type": "answer", "text": "yes"})["type"] == "error")


def test_show_frame_specialist():
    spec = FakeSpecialist("contamination", GREASE)
    brain, fake = make_graph([ai("request_new_view", SHOW, "c_show"), ai("give_verdict", BOX_VERDICT, "c_v")],
                             specialists={"contamination": spec})
    turn = brain.start(frame(mark="closed"), "en")
    check("show: pauses with a show turn", turn["type"] == "show" and turn["show"]["action"] == "open_show_inside", str(turn))
    turn2 = brain.reply(turn["session_id"], {"type": "frame", "image": frame(color=(120, 90, 40), mark="open")})
    check("show: verdict after the new frame", turn2["type"] == "verdict" and turn2["verdict"]["primary_bin"] == "compost", str(turn2))
    tail = fake.requests[1][-2:]
    check("new frame: a text-only tool message, then a human message with the picture",
          isinstance(tail[0], ToolMessage) and isinstance(tail[0].content, str) and isinstance(tail[1], HumanMessage) and has_image(tail[1]))
    report = " ".join(b.get("text", "") for b in tail[1].content if isinstance(b, dict))
    check("pre-armed specialist ran once and its report reached the model", len(spec.calls) == 1 and "Specialist report" in report and "heavy" in report)
    check("specialist shows in the trace", any(e["kind"] == "specialist" for e in turn2["trace"]))


def test_specialist_node_and_unchanged_frame():
    spec = FakeSpecialist("label", {"text_found": ["PLA 7", "COMPOSTABLE"], "resin_code": "7", "compostable_marking": "yes",
                                    "material_stated": "PLA", "hazard_marking": "", "evidence": "printed on base", "confidence": "high"})
    show = {**SHOW, "action": "show_bottom", "say": "Show me the bottom", "then_check": "none", "item_seen": "Clear cup"}
    brain, fake = make_graph([
        ai("request_new_view", show, "c1"),
        ai("run_specialist", {"checks": ["label"], "focus": "base of the cup"}, "c2"),
        ai("give_verdict", verdict([{"item": "compostable cup", "bin": "compost"}], "It is marked compostable"), "c3"),
    ], specialists={"label": spec})
    same = frame(mark="cup")
    turn = brain.start(same, "en")
    turn2 = brain.reply(turn["session_id"], {"type": "frame", "image": same})
    check("specialist node: verdict reached", turn2["type"] == "verdict", str(turn2))
    note = fake.requests[1][-2].content
    check("an unchanged frame is flagged to the model", "practically identical" in note, note)
    result = fake.requests[2][-1]
    check("the check's report comes back as a tool message", isinstance(result, ToolMessage) and result.tool_call_id == "c2" and "COMPOSTABLE" in result.content)
    check("a specialist check does not use up a request to the person", brain.session_log(turn["session_id"])["person_turns"] == 1)


def test_budget_enforced():
    brain, fake = make_graph([
        ai("ask_person", ASK, "a1"),
        ai("ask_person", {**ASK, "question": "Is it empty"}, "a2"),
        ai("ask_person", {**ASK, "question": "Are you sure"}, "a3"),          # over the limit
        ai("give_verdict", verdict([{"item": "soda can", "bin": "recycle", "prep": "Pour out any liquid"}]), "v"),
    ], max_person_turns=2)
    turn = brain.start(frame(), "en")
    turn = brain.reply(turn["session_id"], {"type": "answer", "text": "huh?"})
    check("limit: second question allowed", turn["type"] == "ask")
    turn = brain.reply(turn["session_id"], {"type": "answer", "text": "what?"})
    check("limit: third question blocked, verdict forced", turn["type"] == "verdict", str(turn))
    blocked = fake.requests[3][-1]
    check("limit: the model is told to decide", isinstance(blocked, ToolMessage) and blocked.status == "error" and "used all your requests" in blocked.content)
    check("limit: the person was asked only twice", brain.session_log(turn["session_id"])["person_turns"] == 2)


def test_timeout_and_nudge():
    brain, fake = make_graph([
        ai("ask_person", ASK, "a1"),
        AIMessage(content="I think it goes in recycling."),                    # forgot to call a tool
        ai("give_verdict", verdict([{"item": "soda can", "bin": "recycle", "prep": "Pour out any liquid"}]), "v"),
    ])
    turn = brain.start(frame(), "en")
    turn2 = brain.reply(turn["session_id"], {"type": "timeout"})
    check("timeout: still ends with a verdict", turn2["type"] == "verdict", str(turn2))
    check("timeout: the model is told nobody answered", "did not answer in time" in fake.requests[1][-1].content)
    nudge = fake.requests[2][-1]
    check("nudge: the model is reminded to call a tool", isinstance(nudge, HumanMessage) and str(nudge.content).startswith("Reminder"))


def test_failures_end_safely():
    brain, _ = make_graph([RuntimeError("connection reset by peer")])
    turn = brain.start(frame(), "en")
    check("provider error: safe error turn", turn["type"] == "error" and "labels" in turn["say"] and "connection" in turn["error"], str(turn))

    import anthropic
    from types import SimpleNamespace
    brain, _ = make_graph([anthropic.APIConnectionError(request=SimpleNamespace())])
    turn = brain.start(frame(), "en")
    check("network failure is named the same way as in the classic brain", turn["type"] == "error" and turn["error"] == "no connection to the API", str(turn))

    brain, _ = make_graph([AIMessage(content="a")] * 3)
    check("no decision after two reminders: safe error turn", brain.start(frame(), "en")["type"] == "error")

    brain, _ = make_graph([])
    turn = brain.start("not-an-image", "en")
    check("bad image: safe error turn", turn["type"] == "error" and "bad image" in turn["error"])
    check("unknown session: safe error turn", brain.reply("s_nope", {"type": "timeout"})["type"] == "error")

    brain, _ = make_graph([ai("ask_person", ASK, "a1")])
    turn = brain.start(frame(), "en")
    turn2 = brain.reply(turn["session_id"], {"type": "frame", "image": "garbage"})
    check("bad image in a reply: safe error turn", turn2["type"] == "error" and "bad image" in turn2["error"], str(turn2))

    brain, fake = make_graph([ai("give_verdict", {"items": [], "reason": "x", "confidence": "high"}, "v0"),
                              ai("give_verdict", verdict([{"item": "can", "bin": "recycle"}]), "v1")])
    turn = brain.start(frame(), "en")
    check("an empty verdict is sent back for a retry", turn["type"] == "verdict" and len(fake.requests) == 2)

    brain, _ = make_graph([ai("ask_person", ASK, "a1")])
    turn = brain.start(frame(), "en")
    brain.end(turn["session_id"])
    check("end() forgets the session", brain.session_log(turn["session_id"]) is None)


def test_same_turns_as_classic_brain():
    """Same model decisions in, same Turn dicts out, on both orchestrators."""
    spec_result = GREASE
    cases = {
        "question flow": (
            [("ask_person", ASK), ("give_verdict", CAN_VERDICT)],
            [{"type": "answer", "text": "yes"}]),
        "second-look flow with the pre-armed check": (
            [("request_new_view", SHOW), ("give_verdict", BOX_VERDICT)],
            [{"type": "frame", "image": frame(color=(120, 90, 40), mark="open")}]),
        "no answer": (
            [("ask_person", ASK), ("give_verdict", CAN_VERDICT)],
            [{"type": "timeout"}]),
        "two bins": ([("give_verdict", verdict([{"item": "leftover food", "bin": "compost"}, {"item": "foam box", "bin": "landfill"}],
                                               "Foam cannot be recycled here"))], []),
        "safety item": ([("give_verdict", verdict([{"item": "batteries", "bin": "special", "special_dest": "the battery drop-off box"}],
                                                  "Batteries can start fires"))], []),
        "nothing to sort": ([("nothing_to_sort", {"what_i_see": "an empty counter", "say": "Hold your item up to the camera"})], []),
    }
    for label, (moves, replies) in cases.items():
        classic, _ = make_brain([response(tool(n, a, f"t{i}")) for i, (n, a) in enumerate(moves)],
                                specialists={"contamination": FakeSpecialist("contamination", spec_result)})
        graph, _ = make_graph([ai(n, a, f"t{i}") for i, (n, a) in enumerate(moves)],
                              specialists={"contamination": FakeSpecialist("contamination", spec_result)})
        start = frame(mark="closed")
        a, b = classic.start(start, "en"), graph.start(start, "en")
        check(f"same first turn: {label}", comparable(a) == comparable(b), json.dumps([comparable(a), comparable(b)])[:600])
        for payload in replies:
            a, b = classic.reply(a["session_id"], payload), graph.reply(b["session_id"], payload)
            check(f"same next turn: {label}", comparable(a) == comparable(b), json.dumps([comparable(a), comparable(b)])[:600])
    classic, _ = make_brain([response(tool("give_verdict", verdict([{"item": "lata", "bin": "recycle"}], "Las latas se reciclan siempre")))])
    graph, _ = make_graph([ai("give_verdict", verdict([{"item": "lata", "bin": "recycle"}], "Las latas se reciclan siempre"))])
    check("same Spanish verdict", comparable(classic.start(frame(), "es")) == comparable(graph.start(frame(), "es")))


def test_providers():
    s = Settings()
    check("default settings mean Claude", providers.resolve(s) == ("anthropic", "claude-opus-5-5"))
    check("a gemini model id means Google", providers.resolve(Settings(model="gemini-3.8-flash")) == ("google", "gemini-3.8-flash"))
    check("provider google uses the configured Gemini model", providers.resolve(Settings(provider="google")) == ("google", s.gemini_model))
    tools = build_tools(load_station("3bin"))
    google = providers.tools_for(tools, "google")
    flat = json.dumps(google)
    check("Gemini tools: no keywords it rejects", "additionalProperties" not in flat and '"strict"' not in flat)
    check("Gemini tools: every tool and its required fields survive",
          [t["function"]["name"] for t in google] == [t["name"] for t in tools]
          and google[3]["function"]["parameters"]["required"] == tools[3]["input_schema"]["required"])
    check("Claude tools pass through unchanged, strict", providers.tools_for(tools, "anthropic") is tools and all(t.get("strict") for t in tools))
    msg = AIMessage(content=[{"type": "text", "text": "hello"}],
                    usage_metadata={"input_tokens": 1000, "output_tokens": 50, "total_tokens": 1050,
                                    "input_token_details": {"cache_read": 600, "cache_creation": 300}})
    used = providers.usage_of(msg)
    check("usage: cached tokens are split out of the input total",
          (used.input_tokens, used.cache_read_input_tokens, used.cache_creation_input_tokens, used.output_tokens) == (100, 600, 300, 50))
    check("text is read from block content", providers.text_of(msg) == "hello")
    split = AIMessage(content="", usage_metadata={"input_tokens": 5200, "output_tokens": 10, "total_tokens": 5210,
                                                  "input_token_details": {"cache_read": 0, "cache_creation": 0, "ephemeral_5m_input_tokens": 5000}})
    used = providers.usage_of(split)
    check("usage: a cache write reported per lifetime is still counted as a cache write",
          (used.input_tokens, used.cache_creation_input_tokens) == (200, 5000))
    brain, _ = make_graph([ai("give_verdict", verdict([{"item": "napkin", "bin": "landfill"}], "No compost bin here"))], station_id="2bin")
    turn = brain.start(frame(), "en")
    check("two-bin station works on the graph brain", turn["verdict"]["steps"][0]["position"] == "right")
    gem, fake = make_graph([ai("give_verdict", verdict([{"item": "can", "bin": "recycle"}]))], model="gemini-3.8-flash")
    turn = gem.start(frame(), "en")
    check("with a Gemini model id the instructions go as plain text and the tools are converted",
          turn["type"] == "verdict" and isinstance(fake.requests[0][0].content, str) and fake.bound[0][0].get("type") == "function")


def main() -> int:
    tests = [test_ask_then_verdict, test_show_frame_specialist, test_specialist_node_and_unchanged_frame, test_budget_enforced,
             test_timeout_and_nudge, test_failures_end_safely, test_same_turns_as_classic_brain, test_providers]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"ok    {fn.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL  {fn.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(PASSED)} checks passed, {failed} test group(s) failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
