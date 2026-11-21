"""Offline checks of Sorty's decision loop, turn format and server.

No API key and no network needed: Claude is replaced by a scripted fake, so
these verify the plumbing and the guardrails (request budget, safe fallbacks,
message format), not the model's judgement. The live judgement tests are in
run_scenarios.py.

    python -m tests.test_offline      (from the sorty folder)
"""
from __future__ import annotations

import base64
import io
import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw  # noqa: E402

from brain.agent import Brain  # noqa: E402
from brain.config import Settings, load_station  # noqa: E402
from brain.llm import LLM  # noqa: E402
from brain.mock_brain import MockBrain  # noqa: E402
from brain.tools import build_tools  # noqa: E402

PASSED: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if not condition:
        raise AssertionError(f"{name} FAILED {detail}")
    PASSED.append(name)


def frame(color=(200, 60, 40), mark: str = "A") -> str:
    img = Image.new("RGB", (640, 480), (225, 225, 225))
    draw = ImageDraw.Draw(img)
    draw.rectangle((220, 120, 420, 380), fill=color)
    draw.text((300, 230), mark, fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def tool(name: str, args: dict, id_: str = "toolu_1"):
    return SimpleNamespace(type="tool_use", name=name, input=args, id=id_)


def text(t: str):
    return SimpleNamespace(type="text", text=t)


def thinking():
    return SimpleNamespace(type="thinking", thinking="", signature="sig")


def response(*blocks, stop_reason: str = "tool_use"):
    usage = SimpleNamespace(input_tokens=1000, output_tokens=50, cache_read_input_tokens=0, cache_creation_input_tokens=0)
    return SimpleNamespace(content=list(blocks), stop_reason=stop_reason, usage=usage)


class FakeClient:
    """Stands in for anthropic.Anthropic: returns scripted responses in order."""

    def __init__(self, script: list) -> None:
        self.script = list(script)
        self.requests: list[dict] = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **params):
        # Snapshot the message list as it was sent.
        self.requests.append({**params, "messages": list(params["messages"])})
        if not self.script:
            raise AssertionError("fake model ran out of scripted responses")
        item = self.script.pop(0)
        return item(params) if callable(item) else item


class FakeSpecialist:
    def __init__(self, name: str, result: dict) -> None:
        self.name, self.result, self.calls = name, result, []

    def run(self, frame_bytes: bytes, focus: str) -> dict:
        self.calls.append(focus)
        return self.result


def make_brain(script: list, station_id: str = "3bin", specialists: dict | None = None, **overrides):
    settings = Settings(station_id=station_id, **overrides)
    client = FakeClient(script)
    llm = LLM(settings, client=client)
    brain = Brain(settings, llm=llm, specialists=specialists or {}, station=load_station(station_id))
    return brain, client


ASK = {"question": "Is there liquid inside", "kind": "yes_no", "options": [], "because": "I can't see inside the can.",
       "item_seen": "Soda can", "fact": "liquid inside"}
SHOW = {"action": "open_show_inside", "say": "open the box and show me inside", "because": "I can't see the inside.",
        "item_seen": "Pizza box", "then_check": "contamination"}


def verdict(items, reason="Empty cans recycle again and again", confidence="high"):
    return {"items": [{"prep": "", "special_dest": "", **i} for i in items], "reason": reason, "confidence": confidence}


def last_user(client: FakeClient, index: int = -1) -> dict:
    return client.requests[index]["messages"][-1]


# ---------------------------------------------------------------------------
def test_ask_then_verdict():
    brain, client = make_brain([
        response(thinking(), tool("ask_person", ASK, "toolu_ask")),
        response(tool("give_verdict", verdict([{"item": "soda can", "bin": "recycle", "prep": "Pour out the soda"}],
                                               "Liquid spoils the recycling"), "toolu_v")),
    ])
    turn = brain.start(frame(), "en")
    check("ask: turn type", turn["type"] == "ask", str(turn))
    check("ask: question punctuated and spoken", turn["say"] == "Is there liquid inside?", turn["say"])
    check("ask: yes/no/unsure buttons", [o["id"] for o in turn["ask"]["options"]] == ["yes", "no", "unsure"])
    check("ask: item label", turn["display"]["item_label"] == "Soda can")
    check("ask: the reason is shown", turn["display"]["sub"] == "I can't see inside the can.")
    first = client.requests[0]
    check("request: strict tools sent", all(t.get("strict") for t in first["tools"]))
    check("request: one tool per turn", first["tool_choice"] == {"type": "auto", "disable_parallel_tool_use": True})
    check("request: adaptive thinking + effort", first["thinking"] == {"type": "adaptive"} and first["output_config"]["effort"] == "low")
    check("request: refusal fallback enabled", first.get("fallbacks") == "default" and first.get("betas"))
    check("request: first message carries an image", any(b.get("type") == "image" for b in first["messages"][0]["content"]))
    check("request: system prompt cached", first["system"][0].get("cache_control") == {"type": "ephemeral"})

    turn2 = brain.reply(turn["session_id"], {"type": "answer", "text": "yes"})
    check("verdict: turn type", turn2["type"] == "verdict", str(turn2))
    check("verdict: wording", turn2["say"] == "First, pour out the soda. Then: blue bin, on your left. Liquid spoils the recycling. Thank you!", turn2["say"])
    steps = turn2["verdict"]["steps"]
    check("verdict: prep step then bin step", [s["kind"] for s in steps] == ["prep", "bin"], str(steps))
    check("verdict: bin step position", steps[1]["bin"] == "recycle" and steps[1]["position"] == "left")
    sent = last_user(client)
    check("history: assistant turn kept whole (thinking included)",
          client.requests[1]["messages"][1]["role"] == "assistant" and len(client.requests[1]["messages"][1]["content"]) == 2)
    check("history: answer returned as tool_result for the right call",
          sent["role"] == "user" and sent["content"][0]["type"] == "tool_result" and sent["content"][0]["tool_use_id"] == "toolu_ask")
    check("history: answer text quoted", 'The person answered: "yes"' in sent["content"][0]["content"][0]["text"])
    log = brain.session_log(turn["session_id"])
    check("log: one request to the person", log["person_turns"] == 1)
    check("trace: has ask, answer, verdict", [e["kind"] for e in turn2["trace"]] == ["frame", "ask", "answer", "verdict"], str(turn2["trace"]))
    again = brain.reply(turn["session_id"], {"type": "answer", "text": "yes"})
    check("finished session rejects further replies", again["type"] == "error")


def test_show_frame_specialist():
    spec = FakeSpecialist("contamination", {"surface_inspected": "inside of box", "surface_visible": "yes",
                                            "food_or_grease_present": "yes", "severity": "heavy", "coverage_percent": 45,
                                            "liquid_visible": "no", "evidence": "dark translucent patches", "confidence": "high"})
    brain, client = make_brain([
        response(tool("request_new_view", SHOW, "toolu_show")),
        response(tool("give_verdict", verdict([{"item": "greasy pizza box", "bin": "compost"}], "Grease spoils paper recycling"), "toolu_v")),
    ], specialists={"contamination": spec})
    turn = brain.start(frame(mark="closed"), "en")
    check("show: turn type", turn["type"] == "show", str(turn))
    check("show: instruction capitalised with full stop", turn["say"] == "Open the box and show me inside.", turn["say"])
    check("show: action and icon", turn["show"]["action"] == "open_show_inside" and turn["display"]["icon"] == "open")
    turn2 = brain.reply(turn["session_id"], {"type": "frame", "image": frame(color=(120, 90, 40), mark="open")})
    check("show: verdict after new frame", turn2["type"] == "verdict" and turn2["verdict"]["primary_bin"] == "compost", str(turn2))
    check("show: verdict arrow is centre", turn2["verdict"]["steps"][0]["position"] == "center")
    check("show: verdict wording", turn2["say"] == "Green bin, in the middle. Grease spoils paper recycling. Thank you!", turn2["say"])
    result_blocks = last_user(client)["content"][0]["content"]
    kinds = [b["type"] for b in result_blocks]
    check("show: new frame sent back inside the tool result", kinds == ["text", "image", "text"], str(kinds))
    check("show: pre-armed specialist ran once on the new frame", len(spec.calls) == 1)
    check("show: specialist report included", "Specialist report" in result_blocks[2]["text"] and "heavy" in result_blocks[2]["text"])
    check("show: specialist in trace", any(e["kind"] == "specialist" for e in turn2["trace"]))


def test_on_demand_specialist_and_unchanged_frame():
    spec = FakeSpecialist("label", {"text_found": ["PLA 7", "COMPOSTABLE"], "resin_code": "7", "compostable_marking": "yes",
                                    "material_stated": "PLA", "hazard_marking": "", "evidence": "printed on base", "confidence": "high"})
    show = {**SHOW, "action": "show_bottom", "say": "Show me the bottom", "then_check": "none", "item_seen": "Clear cup"}
    brain, client = make_brain([
        response(tool("request_new_view", show, "t1")),
        response(tool("run_specialist", {"checks": ["label"], "focus": "base of the cup"}, "t2")),
        response(tool("give_verdict", verdict([{"item": "compostable cup", "bin": "compost"}], "It is marked compostable"), "t3")),
    ], specialists={"label": spec})
    same = frame(mark="cup")
    turn = brain.start(same, "en")
    turn2 = brain.reply(turn["session_id"], {"type": "frame", "image": same})
    check("specialist on demand: verdict reached", turn2["type"] == "verdict", str(turn2))
    note = client.requests[1]["messages"][-1]["content"][0]["content"][0]["text"]
    check("unchanged frame is flagged to the model", "practically identical" in note, note)
    spec_result = client.requests[2]["messages"][-1]["content"][0]
    check("specialist result returned as tool_result", spec_result["tool_use_id"] == "t2" and "COMPOSTABLE" in spec_result["content"])
    check("specialist does not use a person request", brain.session_log(turn["session_id"])["person_turns"] == 1)


def test_budget_enforced():
    brain, client = make_brain([
        response(tool("ask_person", ASK, "a1")),
        response(tool("ask_person", {**ASK, "question": "Is it empty"}, "a2")),
        response(tool("ask_person", {**ASK, "question": "Are you sure"}, "a3")),      # over budget
        response(tool("give_verdict", verdict([{"item": "soda can", "bin": "recycle", "prep": "Pour out any liquid"}]), "v")),
    ], max_person_turns=2)
    turn = brain.start(frame(), "en")
    turn = brain.reply(turn["session_id"], {"type": "answer", "text": "huh?"})
    check("budget: second question allowed", turn["type"] == "ask")
    turn = brain.reply(turn["session_id"], {"type": "answer", "text": "what?"})
    check("budget: third question blocked, verdict forced", turn["type"] == "verdict", str(turn))
    blocked = client.requests[3]["messages"][-1]["content"][0]
    check("budget: model told to decide", blocked.get("is_error") and "used all your requests" in blocked["content"])
    check("budget: person asked only twice", brain.session_log(turn["session_id"])["person_turns"] == 2)


def test_timeout_and_no_tool_nudge():
    brain, client = make_brain([
        response(tool("ask_person", ASK, "a1")),
        response(text("I think it goes in recycling."), stop_reason="end_turn"),       # forgot to call a tool
        response(tool("give_verdict", verdict([{"item": "soda can", "bin": "recycle", "prep": "Pour out any liquid"}]), "v")),
    ])
    turn = brain.start(frame(), "en")
    turn2 = brain.reply(turn["session_id"], {"type": "timeout"})
    check("timeout: still ends with a verdict", turn2["type"] == "verdict", str(turn2))
    told = client.requests[1]["messages"][-1]["content"][0]["content"][0]["text"]
    check("timeout: model told the person did not answer", "did not answer in time" in told, told)
    check("nudge: model reminded to call a tool", client.requests[2]["messages"][-1]["content"].startswith("Reminder"))


def test_failures_end_safely():
    brain, _ = make_brain([response(stop_reason="refusal")])
    turn = brain.start(frame(), "en")
    check("refusal: safe error turn", turn["type"] == "error" and "labels" in turn["say"], str(turn))

    brain, _ = make_brain([response(text("a"), stop_reason="end_turn")] * 3)
    turn = brain.start(frame(), "en")
    check("no decision after nudges: safe error turn", turn["type"] == "error")

    brain, _ = make_brain([])
    turn = brain.start("not-an-image", "en")
    check("bad image: safe error turn", turn["type"] == "error" and "bad image" in turn["error"])
    check("unknown session: safe error turn", brain.reply("s_nope", {"type": "timeout"})["type"] == "error")

    import anthropic
    def boom(params):
        raise anthropic.APIConnectionError(request=SimpleNamespace())
    brain, _ = make_brain([boom])
    turn = brain.start(frame(), "en")
    check("network failure: safe error turn", turn["type"] == "error" and "connection" in turn["error"], str(turn))

    brain, client = make_brain([
        response(tool("give_verdict", {"items": [], "reason": "x", "confidence": "high"}, "v0")),
        response(tool("give_verdict", verdict([{"item": "can", "bin": "recycle"}]), "v1")),
    ])
    turn = brain.start(frame(), "en")
    check("empty verdict is sent back for a retry", turn["type"] == "verdict" and len(client.requests) == 2)


def test_verdict_forms():
    brain, _ = make_brain([response(tool("give_verdict", verdict(
        [{"item": "leftover food", "bin": "compost"}, {"item": "foam box", "bin": "landfill"}], "Foam cannot be recycled here")))])
    turn = brain.start(frame(), "en")
    check("two items: wording", turn["say"] == "Leftover food: green bin, in the middle. Foam box: black bin, on your right. Foam cannot be recycled here. Thank you!", turn["say"])
    check("two items: two bin steps", [s["bin"] for s in turn["verdict"]["steps"]] == ["compost", "landfill"])

    brain, _ = make_brain([response(tool("give_verdict", verdict(
        [{"item": "batteries", "bin": "special", "special_dest": "the battery drop-off box"}], "Batteries can start fires")))])
    turn = brain.start(frame(), "en")
    check("special: wording", turn["say"] == "Not in these bins. Please use the battery drop-off box. Batteries can start fires. Thank you!", turn["say"])
    check("special: step and warning icon", turn["verdict"]["steps"][0]["kind"] == "special" and turn["display"]["icon"] == "warning"
          and turn["verdict"]["special_dest"] == "The battery drop-off box")

    brain, _ = make_brain([response(tool("give_verdict", verdict([{"item": "keys", "bin": "not_trash"}], "Keys are worth keeping")))])
    turn = brain.start(frame(), "en")
    check("not trash: wording, no thanks", turn["say"] == "That doesn't look like trash. Keys are worth keeping.", turn["say"])

    brain, _ = make_brain([response(tool("give_verdict", verdict([{"item": "lata", "bin": "recycle"}], "Las latas se reciclan siempre")))])
    turn = brain.start(frame(), "es")
    check("spanish: wording", turn["say"] == "Contenedor azul, a tu izquierda. Las latas se reciclan siempre. ¡Gracias!", turn["say"])

    brain, _ = make_brain([response(tool("nothing_to_sort", {"what_i_see": "an empty counter", "say": "Hold your item up to the camera"}))])
    turn = brain.start(frame(), "en")
    check("nothing to sort: quiet turn", turn["type"] == "no_item" and turn["say"] == "Hold your item up to the camera.")


def test_two_bin_station():
    station = load_station("2bin")
    enum = build_tools(station)[3]["input_schema"]["properties"]["items"]["items"]["properties"]["bin"]["enum"]
    check("2-bin station: compost cannot be named", enum == ["recycle", "landfill", "special", "not_trash"], str(enum))
    brain, client = make_brain([response(tool("give_verdict", verdict([{"item": "napkin", "bin": "landfill"}], "No compost bin here")))], station_id="2bin")
    turn = brain.start(frame(), "en")
    check("2-bin station: right-hand bin", turn["verdict"]["steps"][0]["position"] == "right" and "black bin, on your right" in turn["say"].lower())
    check("2-bin station: prompt lists two bins", '"compost"' not in client.requests[0]["system"][0]["text"])


def test_mock_brain():
    scenarios = json.loads((ROOT / "tests" / "scenarios.json").read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in scenarios["scenarios"]}
    check("scenario ids are unique", len(by_id) == len(scenarios["scenarios"]))
    mock = MockBrain(Settings(), load_station("3bin"), by_id, delay_s=0)
    turn = mock.start(frame(), "en", "pizza_box_greasy")
    check("mock: pizza box asks for a new view", turn["type"] == "show" and turn["show"]["action"] == "open_show_inside")
    turn = mock.reply(turn["session_id"], {"type": "frame", "image": frame()})
    check("mock: pizza box verdict", turn["type"] == "verdict" and turn["verdict"]["primary_bin"] == "compost")
    turn = mock.start(frame(), "en", "soda_can_liquid")
    check("mock: soda can asks", turn["type"] == "ask")
    turn = mock.reply(turn["session_id"], {"type": "answer", "text": "yes"})
    check("mock: soda can verdict has a prep step", turn["verdict"]["steps"][0]["kind"] == "prep")
    for sid in by_id:                      # every scenario must produce a playable script
        t = mock.start(frame(), "en", sid)
        hops = 0
        while t["type"] in ("ask", "show") and hops < 5:
            t = mock.reply(t["session_id"], {"type": "answer", "text": "yes"})
            hops += 1
        check(f"mock: scenario {sid} reaches a verdict", t["type"] == "verdict", str(t)[:200])
    two = MockBrain(Settings(station_id="2bin"), load_station("2bin"), by_id, delay_s=0)
    t = two.start(frame(), "en", "banana_peel")
    check("mock: falls back to an existing bin on a 2-bin station", t["verdict"]["primary_bin"] == "landfill")


def test_server():
    from server.app import make_server
    server, app = make_server(port=0, force_mock=True)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"

    def call(method: str, path: str, payload: dict | None = None):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(base + path, data=data, method=method, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                body = r.read()
                return r.status, (json.loads(body) if "json" in r.headers.get("Content-Type", "") else body)
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    try:
        app.brain.delay_s = 0
        status, cfg = call("GET", "/api/config")
        check("server: config", status == 200 and cfg["mode"] == "mock" and len(cfg["station"]["bins"]) == 3 and cfg["timeouts"]["answer_s"] > 0)
        check("server: starts on the standard AI setup and offers two", cfg["profile"]["name"] == "standard"
              and sorted(o["name"] for o in cfg["profile"]["options"]) == ["fast", "standard"], str(cfg.get("profile")))
        check("server: says practice mode was forced at the start", cfg["why_practice"] == "forced", str(cfg.get("why_practice")))
        status, cfg = call("POST", "/api/profile", {"profile": "fast"})
        check("server: faster setup chosen", status == 200 and cfg["profile"]["name"] == "fast", str(cfg)[:200])
        check("server: faster setup changes the model and drops the pre-armed check",
              app.settings.model == "claude-sonnet-5-5" and app.settings.prearm_specialist is False)
        status, cfg = call("POST", "/api/profile", {"profile": "standard"})
        check("server: standard setup restored", status == 200 and cfg["profile"]["name"] == "standard"
              and app.settings.model == "claude-opus-5-5" and app.settings.prearm_specialist is True, str(cfg)[:200])
        status, err = call("POST", "/api/profile", {"profile": "turbo"})
        check("server: unknown setup is a 400 and changes nothing", status == 400 and "error" in err
              and app.profile == "standard" and app.settings.model == "claude-opus-5-5", str(err))
        status, err = call("POST", "/api/profile", {})
        check("server: missing setup name is a 400", status == 400 and "error" in err, str(err))
        status, cfg = call("POST", "/api/mode", {"mode": "live"})
        check("server: a forced practice start cannot be switched to live", status == 200 and cfg["mode"] == "mock"
              and cfg["why_practice"] == "forced" and app.mode == "mock", str(cfg)[:200])
        status, cfg = call("POST", "/api/mode", {"mode": "practice"})
        check("server: asking it for practice mode is answered and changes nothing", status == 200 and cfg["mode"] == "mock"
              and cfg["why_practice"] == "forced", str(cfg)[:200])
        status, err = call("POST", "/api/mode", {"mode": "offline"})
        check("server: unknown mode is a 400", status == 400 and "error" in err and app.mode == "mock", str(err))
        status, err = call("POST", "/api/mode", {})
        check("server: missing mode is a 400", status == 400 and "error" in err, str(err))
        status, turn = call("POST", "/api/session", {"image": frame(), "lang": "en", "demo_scenario": "soda_can_empty"})
        check("server: start session", status == 200 and turn["type"] == "ask", str(turn)[:200])
        status, turn2 = call("POST", f"/api/session/{turn['session_id']}/reply", {"type": "answer", "text": "no"})
        check("server: reply", status == 200 and turn2["type"] == "verdict")
        status, _ = call("POST", f"/api/session/{turn['session_id']}/end", {})
        check("server: end", status == 200)
        status, err = call("POST", "/api/session", {"lang": "en"})
        check("server: missing image is a 400", status == 400)
        status, ans = call("POST", "/api/demo/answer", {"scenario_id": "soda_can_empty", "question": "Is there liquid inside?"})
        check("server: demo answer", status == 200 and ans["text"])
        status, demo = call("GET", "/api/demo/scenarios")
        check("server: demo scenario list", status == 200 and isinstance(demo, list))
        status, _ = call("GET", "/api/nope")
        check("server: unknown api path is a 404", status == 404)
        status, _ = call("GET", "/demo-images/..%2f..%2f.env")
        check("server: cannot read files outside the image folder", status in (403, 404))
        status, _ = call("GET", "/..%2f.env")
        check("server: cannot read the .env through the kiosk path", status in (403, 404))
        status, _ = call("GET", "/")
        check("server: kiosk root answers", status == 200)
    finally:
        server.shutdown()
        server.server_close()


def test_mode_switch():
    """The practice-mode switch (App.set_mode). Any real key is hidden and the live brain is replaced by a
    stand-in for the whole test, so nothing here can reach the AI."""
    import contextlib
    import os
    import server.app as server_app
    from brain import budget

    class LiveStandIn:                      # takes the place of the live brain: reads no key, builds no client
        mode = "live"

        def __init__(self, *args, **kwargs) -> None:
            pass

    has = {"key": False, "budget_left": True}
    saved = (server_app.has_api_key, server_app.Brain, budget.exhausted, os.environ.get("SORTY_MODE"))
    saved_orchestrator = os.environ.get("SORTY_ORCHESTRATOR")
    os.environ["SORTY_ORCHESTRATOR"] = "classic"    # the stand-in below takes the place of the classic brain
    server_app.has_api_key = lambda: has["key"]
    server_app.Brain = LiveStandIn
    budget.exhausted = lambda: not has["budget_left"]
    os.environ["SORTY_MODE"] = "live"       # a practice-mode setting in the environment would decide everything below
    try:
        with contextlib.redirect_stdout(io.StringIO()):         # the server announces each change of mode
            app = server_app.App(force_mock=False)
            cfg = app.config()
            check("mode switch: no key means practice mode", cfg["mode"] == "mock" and cfg["why_practice"] == "no_key", str(cfg["why_practice"]))
            cfg = app.set_mode("practice")
            check("mode switch: practice mode chosen by hand", cfg["mode"] == "mock" and cfg["why_practice"] == "chosen")
            cfg = app.set_mode("live")
            check("mode switch: without a key it stays in practice mode", cfg["mode"] == "mock" and cfg["why_practice"] == "no_key"
                  and isinstance(app.brain, MockBrain))

            has["key"] = True               # from here a key is "there", and the stand-in is what going live builds
            cfg = app.config()
            check("mode switch: a key ends practice mode by itself", cfg["mode"] == "live" and cfg["why_practice"] is None
                  and isinstance(app.brain, LiveStandIn))
            cfg = app.set_mode("practice")
            check("mode switch: by hand, the scripted brain takes over with the scenarios", cfg["mode"] == "mock"
                  and cfg["why_practice"] == "chosen" and isinstance(app.brain, MockBrain) and app.brain.scenarios == app.scenarios)
            check("mode switch: the next config request does not undo it", app.config()["mode"] == "mock")
            cfg = app.set_mode("live")
            check("mode switch: and back to the AI", cfg["mode"] == "live" and cfg["why_practice"] is None
                  and isinstance(app.brain, LiveStandIn))

            app.set_mode("practice")
            has["budget_left"] = False      # the budget runs out while practice mode is on
            cfg = app.set_mode("live")
            check("mode switch: no budget left, so it stays in practice mode", cfg["mode"] == "mock" and cfg["why_practice"] == "budget")
            has["budget_left"] = True
            cfg = app.set_mode("live")
            check("mode switch: a used-up budget holds until a restart", cfg["mode"] == "mock" and cfg["why_practice"] == "budget")

            app = server_app.App(force_mock=True)
            cfg = app.set_mode("live")
            check("mode switch: a --mock start stays in practice mode", cfg["mode"] == "mock" and cfg["why_practice"] == "forced")
            os.environ["SORTY_MODE"] = "mock"
            cfg = server_app.App(force_mock=False).set_mode("live")
            check("mode switch: so does SORTY_MODE=mock", cfg["mode"] == "mock" and cfg["why_practice"] == "forced")
            for bad in (None, "", "mock", ["live"]):
                try:
                    app.set_mode(bad)
                    refused = False
                except ValueError:
                    refused = True
                check(f"mode switch: {bad!r} is refused", refused and app.mode == "mock")
    finally:
        server_app.has_api_key, server_app.Brain, budget.exhausted = saved[:3]
        if saved_orchestrator is None:
            os.environ.pop("SORTY_ORCHESTRATOR", None)
        else:
            os.environ["SORTY_ORCHESTRATOR"] = saved_orchestrator
        if saved[3] is None:
            os.environ.pop("SORTY_MODE", None)
        else:
            os.environ["SORTY_MODE"] = saved[3]


def test_instant_alert():
    """The fast guard that runs beside the careful brain. A stand-in detector answers, so no AI is called."""
    import time as _time
    import server.app as server_app
    from brain import guard as load_guard
    from brain.config import Settings, load_station

    station = load_station("3bin")

    class Detector:
        model = "stand-in"

        def __init__(self, answer, delay=0.0, fail=False):
            self.answer, self.delay, self.fail, self.calls = answer, delay, fail, 0

        def detect(self, frame_bytes):
            self.calls += 1
            _time.sleep(self.delay)
            if self.fail:
                raise RuntimeError("camera glitch")
            return self.answer

    g = load_guard.LoadGuard(Settings(), station, detector=Detector({"item": "vape pen", "category": "vape", "sure": "yes"}))
    look = g.look(frame())
    check("alert: a sure load-wrecker raises the alert", look["alert"] and look["category"] == "vape", str(look))
    unsure = load_guard.LoadGuard(Settings(), station, detector=Detector({"item": "pen", "category": "vape", "sure": "no"})).look(frame())
    check("alert: an unsure look stays silent", unsure["alert"] is False, str(unsure))
    plain = load_guard.LoadGuard(Settings(), station, detector=Detector({"item": "soda can", "category": "none", "sure": "yes"})).look(frame())
    check("alert: an ordinary item stays silent", plain["alert"] is False, str(plain))
    broken = load_guard.LoadGuard(Settings(), station, detector=Detector({}, fail=True)).look(frame())
    check("alert: a failed look never raises and never alerts", broken["alert"] is False and "error" in broken, str(broken))

    turn = load_guard.alert_turn(station, "vape", "vape pen", "en", 930, "fast check")
    check("alert turn: an ordinary verdict turn with an alert block", turn["type"] == "verdict" and turn["alert"]["harm"] == "fire"
          and turn["alert"]["ms"] == 930 and turn["verdict"]["primary_bin"] == "special", str(turn)[:300])
    check("alert turn: wording for a special item",
          turn["say"] == "Stop! Not in these bins. Vapes hide a battery that starts fires. Please use the battery drop-off box. Thank you!", turn["say"])
    check("alert turn: destination shown", turn["verdict"]["steps"][0]["kind"] == "special"
          and turn["verdict"]["steps"][0]["dest"] == "The battery drop-off box", str(turn["verdict"]["steps"]))
    bag = load_guard.alert_turn(station, "plastic_bag", "", "en", 1000, "fast check")
    check("alert turn: wording for a plastic bag",
          bag["say"] == "Stop! Not in the blue bin. Plastic bags jam the sorting machines. Black bin, on your right. Thank you!", bag["say"])
    check("alert turn: the bag still gets its bin and arrow", bag["verdict"]["primary_bin"] == "landfill"
          and bag["verdict"]["steps"][0]["position"] == "right" and bag["alert"]["avoid_bin"] == "recycle")
    es = load_guard.alert_turn(station, "battery", "pilas", "es", 900, "fast check")
    check("alert turn: Spanish", es["say"].startswith("¡Alto! No va en estos contenedores.") and es["say"].endswith("¡Gracias!"), es["say"])
    two = load_guard.alert_turn(load_station("2bin"), "plastic_bag", "bag", "en", 900, "fast check")
    check("alert turn: works on the two-bin station", two["verdict"]["primary_bin"] == "landfill", str(two["verdict"]))
    check("alert turn: trace explains what happened", [e["kind"] for e in turn["trace"]] == ["frame", "alert", "verdict"])

    # Practice mode: scenarios marked as load-wreckers return the same alert, scripted.
    app = server_app.App(force_mock=True)
    app.brain.delay_s = 0
    t = app.start_session(frame(), "en", "vape")
    check("alert: practice mode shows the alert for a marked scenario", t["type"] == "verdict" and t.get("alert", {}).get("category") == "vape", str(t)[:200])
    t = app.start_session(frame(), "en", "soda_can_empty")
    check("alert: practice mode leaves ordinary scenarios alone", t["type"] == "ask" and "alert" not in t)

    # Live path with stand-ins: both models start together; a sure alert is not held up by the careful brain.
    class SlowBrain:
        mode = "live"

        def __init__(self):
            self.sessions, self.ended = {}, []

        def start(self, image, lang="en", demo=None):
            _time.sleep(0.5)
            return {"session_id": "s_slow", "turn": 1, "type": "verdict", "say": "Blue bin, on your left.",
                    "trace": [{"t_ms": 0, "kind": "frame", "text": "Item presented to the camera"}]}

        def end(self, session_id):
            self.ended.append(session_id)

    saved_key = server_app.has_api_key
    server_app.has_api_key = lambda: True
    try:
        app.brain, app.mode = SlowBrain(), "live"
        app._guard = load_guard.LoadGuard(app.settings, station, detector=Detector({"item": "AA batteries", "category": "battery", "sure": "yes"}))
        t0 = _time.monotonic()
        t = app.start_session(frame(), "en", None)
        fast_s = _time.monotonic() - t0
        check("alert: live, the alert is the answer", t.get("alert", {}).get("category") == "battery", str(t)[:200])
        check("alert: live, it does not wait for the careful brain", fast_s < 0.4, f"{fast_s:.2f} s")
        _time.sleep(0.7)
        check("alert: live, the unused careful session is dropped", app.brain.ended == ["s_slow"], str(app.brain.ended))

        app._guard = load_guard.LoadGuard(app.settings, station, detector=Detector({"item": "soda can", "category": "none", "sure": "yes"}))
        t = app.start_session(frame(), "en", None)
        check("alert: live, a clear fast look hands over to the careful brain", t["say"] == "Blue bin, on your left."
              and t["guard"]["clear"] is True and [e["kind"] for e in t["trace"]] == ["frame", "guard"], str(t)[:300])

        app._guard = load_guard.LoadGuard(app.settings, station, detector=Detector({"item": "?", "category": "battery", "sure": "yes"}, delay=1.5))
        app.settings.guard_wait_s = 4.0
        t = app.start_session(frame(), "en", None)
        check("alert: live, a slow fast look never delays the careful answer", t["say"] == "Blue bin, on your left." and "alert" not in t, str(t)[:200])

        app.settings.guard = False
        app._guard = load_guard.LoadGuard(app.settings, station, detector=Detector({"item": "AA", "category": "battery", "sure": "yes"}))
        t = app.start_session(frame(), "en", None)
        check("alert: switched off, only the careful brain answers", "alert" not in t and "guard" not in t)
    finally:
        server_app.has_api_key = saved_key
        app.settings.guard = True


def test_jev_alert_model():
    """The instant alert on Jev (TypeSafe AI's decision model). A stand-in answers the web call, so nothing
    leaves this machine and no key is needed."""
    import os
    from brain import guard as load_guard
    from brain.config import Settings, load_station
    from brain.imaging import decode_frame

    class Reply:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return json.dumps(self.payload).encode()

    seen = {"calls": 0, "fail": False}

    def opener(request, timeout=None):
        seen["calls"] += 1
        if seen["fail"]:
            raise OSError("no connection")
        seen["url"] = request.full_url
        seen["headers"] = {k.lower(): v for k, v in request.header_items()}
        seen["body"] = json.loads(request.data.decode())
        return Reply(seen["reply"])

    def reply(choice, confidence):
        return {"model": "jev-1.14.0", "answers": {"label": {"type": "choice", "choice": choice, "confidence": confidence,
                                                             "probabilities": {choice: confidence}}},
                "usage": {"input_tokens": 900, "output_tokens": 4}}

    class Net:                                   # stands in for the Claude detector the guard falls back on
        model = "stand-in-net"

        def __init__(self):
            self.calls = 0

        def detect(self, frame_bytes):
            self.calls += 1
            return {"item": "AA batteries", "category": "battery", "sure": "yes"}

    saved_env = {k: os.environ.get(k) for k in load_guard.JEV_KEY_NAMES}
    saved_budget = (load_guard.budget.check, load_guard.budget.add)
    load_guard.budget.check = lambda: None
    load_guard.budget.add = lambda *a, **k: 0.0
    for k in load_guard.JEV_KEY_NAMES:
        os.environ.pop(k, None)
    os.environ["JEV_API_KEY"] = "test-key"
    try:
        s = Settings()
        det = load_guard.JevDetector(s, opener=opener)
        seen["reply"] = reply("vape", 0.93)
        found = det.detect(decode_frame(frame()))
        body, headers = seen["body"], seen["headers"]
        check("jev: calls TypeSafe's decision endpoint", seen["url"] == "https://api.typesafe.ai/v1/systemone", seen["url"])
        check("jev: key sent as a bearer token", headers.get("authorization") == "Bearer test-key")
        check("jev: image input switched on by its header", headers.get("typesafe-danger-zone-images") == "true", str(headers))
        ref = body["state"]["camera"]
        check("jev: the picture is an asset the state refers to", ref in body["assets"] and body["assets"][ref]["format"] == "jpg"
              and len(body["assets"][ref]["data_base64"]) > 100 and body["model"] == "jev-latest")
        q = body["questions"]["label"]
        check("jev: one choice question over the load-wreckers plus none", q["type"] == "choice" and "`camera`" in q["instructions"]
              and set(q["criteria"]) == set(load_guard.WRECKERS) | {"none"}, str(sorted(q["criteria"])))
        check("jev: a confident answer counts as sure", found["category"] == "vape" and found["sure"] == "yes" and found["model"] == "jev-1.14.0", str(found))
        seen["reply"] = reply("vape", 0.55)
        check("jev: a hesitant answer does not", det.detect(decode_frame(frame()))["sure"] == "no")

        station = load_station("3bin")
        g = load_guard.LoadGuard(s, station)
        g.jev, g._claude = load_guard.JevDetector(s, opener=opener), Net()
        seen["reply"] = reply("plastic_bag", 0.97)
        look = g.look(frame())
        check("jev: with a key in .env the alert runs on Jev", look["alert"] and look["category"] == "plastic_bag"
              and look["model"] == "jev-1.14.0" and g._claude.calls == 0 and g.model == "jev-latest", str(look))
        seen["reply"] = reply("none", 0.99)
        check("jev: an ordinary item stays silent", g.look(frame())["alert"] is False)
        seen["fail"] = True
        look = g.look(frame())
        check("jev: if Jev cannot be reached, the Claude alert takes over", look["alert"] and look["category"] == "battery"
              and look.get("fell_back") is True and look["model"] == "stand-in-net", str(look))
        seen["fail"] = False
        s.guard_provider = "claude"
        calls = seen["calls"]
        look = g.look(frame())
        check("jev: can be switched off in favour of Claude", look["model"] == "stand-in-net" and seen["calls"] == calls and "fell_back" not in look)
        s.guard_provider = ""
        os.environ.pop("JEV_API_KEY")
        check("jev: without a key the alert stays on Claude", [type(d).__name__ for d in g.detectors()] == ["Net"]
              and load_guard.active_model(s) == s.guard_model)
    finally:
        load_guard.budget.check, load_guard.budget.add = saved_budget
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def main() -> int:
    tests = [test_ask_then_verdict, test_show_frame_specialist, test_on_demand_specialist_and_unchanged_frame,
             test_budget_enforced, test_timeout_and_no_tool_nudge, test_failures_end_safely, test_verdict_forms,
             test_two_bin_station, test_mock_brain, test_server, test_mode_switch, test_instant_alert,
             test_jev_alert_model]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"ok    {fn.__name__}")
        except Exception as exc:  # report every failing group, not only the first
            failed += 1
            print(f"FAIL  {fn.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(PASSED)} checks passed, {failed} test group(s) failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
