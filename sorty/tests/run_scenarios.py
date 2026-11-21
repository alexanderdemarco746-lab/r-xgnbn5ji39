"""Live scenario tests: run Sorty against the scenario bank with the real model.

For every scenario the camera frames come from tests/images, and a simulated
person answers Sorty's questions from the scenario's hidden facts. The final
verdict is graded against the expected outcome.

With --baseline it also runs a "one-look camera": the same model and the same
rules, but it must answer from the first picture alone (no questions, no
second look, no specialist checks). Comparing the two shows what the
interaction buys.

    python -m tests.run_scenarios                      all scenarios
    python -m tests.run_scenarios --baseline           plus the one-look comparison
    python -m tests.run_scenarios --only soda_can_empty,pizza_box_greasy
    python -m tests.run_scenarios --station 2bin       the 2-bin profile subset

Every run calls the Claude API and costs money; the estimate is printed.
"""
from __future__ import annotations

import argparse
import base64
import copy
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from brain import Brain, get_settings, has_api_key, load_station  # noqa: E402
from brain.llm import LLM  # noqa: E402
from brain.persona import simulated_answer  # noqa: E402

IMAGES = ROOT / "tests" / "images"
RESULTS = ROOT / "tests" / "results"
MAX_HOPS = 8


def b64(name: str) -> str:
    return base64.b64encode((IMAGES / name).read_bytes()).decode("ascii")


# ------------------------------------------------------------------ running
def run_one(brain: Brain, llm: LLM, sc: dict, interactive: bool = True) -> dict:
    """Play one scenario through to its end and return the record."""
    person = sc.get("person", {})
    frames = sc["frames"]
    lang = sc.get("lang", "en")
    script = list(person.get("script") or [])
    transcript, seconds = [], 0.0
    t_wall = time.monotonic()

    turn = brain.start(b64(frames["initial"]), lang, sc["id"])
    hops = spoken = 0
    while True:
        seconds += turn.get("timing_ms", 0) / 1000
        transcript.append({"sorty": turn["type"], "say": turn["say"],
                           **({"action": turn["show"]["action"]} if turn["type"] == "show" else {})})
        if turn["type"] not in ("ask", "show") or hops >= MAX_HOPS:
            break
        hops += 1
        if person.get("timeouts"):
            payload, shown = {"type": "timeout"}, "(no response)"
        elif turn["type"] == "show" and turn["show"]["action"] in frames:
            name = frames[turn["show"]["action"]]
            payload, shown = {"type": "frame", "image": b64(name)}, f"(shows {name})"
        elif turn["type"] == "show" and not script:
            payload, shown = {"type": "frame", "image": b64(frames["initial"])}, "(does not move the item)"
        else:
            if script:
                text = script[min(spoken, len(script) - 1)]
                spoken += 1
            else:
                text = simulated_answer(llm, brain.s, person.get("facts", ""), turn["say"], lang)
            payload, shown = {"type": "answer", "text": text}, text
        transcript.append({"person": shown})
        turn = brain.reply(turn["session_id"], payload)

    log = brain.session_log(turn["session_id"]) or {"person_turns": 0, "specialist_calls": 0, "model_calls": 0, "events": []}
    brain.end(turn["session_id"])
    return {
        "id": sc["id"], "title": sc["title"], "group": sc.get("group", ""),
        "final": turn, "transcript": transcript,
        "person_turns": log["person_turns"], "specialist_calls": log["specialist_calls"],
        "model_calls": log["model_calls"], "events": log["events"],
        "think_seconds": round(seconds, 1), "wall_seconds": round(time.monotonic() - t_wall, 1),
        "interactive": interactive,
    }


# ------------------------------------------------------------------ grading
def _verdict_bins(turn: dict) -> list[str]:
    bins = []
    for step in turn.get("verdict", {}).get("steps", []):
        if step["kind"] == "bin":
            bins.append(step["bin"])
        elif step["kind"] == "special":
            bins.append("special")
        elif step["kind"] == "keep":
            bins.append("not_trash")
    return bins


def _words(turn: dict) -> str:
    v = turn.get("verdict", {})
    parts = [turn.get("say", ""), v.get("reason", "")] + [s.get("text", "") + " " + s.get("dest", "") for s in v.get("steps", [])]
    return " ".join(parts).lower()


def grade(expect: dict, record: dict, station: dict, behaviour: bool = True) -> list[str]:
    """Return the list of problems; empty means the scenario passed."""
    turn = record["final"]
    problems: list[str] = []
    want_type = expect.get("type", "verdict")
    if turn["type"] != want_type:
        why = f" ({turn.get('error')})" if turn.get("error") else ""
        return [f"ended with '{turn['type']}'{why}, expected '{want_type}'"]
    if want_type != "verdict":
        return problems

    bins = _verdict_bins(turn)
    words = _words(turn)
    allowed = set(expect.get("bins", [])) | set(expect.get("also_ok", []))
    for b in bins:
        if b not in allowed:
            problems.append(f"sent something to '{b}' (correct: {' or '.join(expect.get('bins', []))})")
    for b in expect.get("not_bins", []):
        if b in bins:
            problems.append(f"must not use '{b}'")
    labels = {b["id"]: [b["color_name"]["en"], b["label"]["en"].lower(), b["color_name"].get("es", ""), b["label"].get("es", "").lower()]
              for b in station["bins"]}
    for b in expect.get("require_all_bins", []):
        named = b in bins or any(w and w in words for w in labels.get(b, []))
        if not named:
            problems.append(f"did not send anything to '{b}'")
    if expect.get("prep_mentions") and not any(k in words for k in expect["prep_mentions"]):
        problems.append("did not tell the person to empty it first")
    for b, keys in (expect.get("prep_mentions_for") or {}).items():
        if b in bins and not any(k in words for k in keys):
            problems.append(f"chose '{b}' without telling the person to empty it first")
    if expect.get("dest_mentions") and not any(k in words for k in expect["dest_mentions"]):
        problems.append("did not say where it should go instead")
    if expect.get("say_contains_any") and not any(k in words for k in expect["say_contains_any"]):
        problems.append("did not answer in the expected language")

    if behaviour:
        asked = any(e["event"] == "ask" for e in record["events"])
        viewed = any(e["event"] == "show" for e in record["events"])
        needs = expect.get("needs")
        if needs == "ask" and not asked:
            problems.append("should have asked the person (no camera can see this)")
        if needs == "view" and not viewed:
            problems.append("should have asked for another view")
        if needs == "info" and not (asked or viewed):
            problems.append("decided without finding out the hidden fact")
        if needs == "none" and record["person_turns"] > 0:
            problems.append("bothered the person although the answer was visible")
        limit = expect.get("max_person_turns")
        if limit is not None and record["person_turns"] > limit:
            problems.append(f"made {record['person_turns']} requests to the person (limit {limit})")
    return problems


# ---------------------------------------------------------------- reporting
def summarise(record: dict) -> str:
    turn = record["final"]
    if turn["type"] != "verdict":
        return f"[{turn['type']}] {turn['say']}"
    return turn["say"]


def write_report(path: Path, meta: dict, sorty: list[dict], baseline: list[dict] | None) -> None:
    n = len(sorty)
    passed = sum(1 for r in sorty if r["passed"])
    lines = ["# Sorty scenario test report", ""]
    lines.append(f"Run: {meta['when']}  |  model: `{meta['model']}` (effort {meta['effort']})  |  station: {meta['station']}  |  "
                 f"images: Blender renders in `tests/images`  |  estimated API cost of this run: ${meta['cost_usd']:.2f}")
    lines.append("")
    lines.append("## Result")
    lines.append("")
    lines.append(f"**Sorty got {passed} of {n} scenarios right.**")
    if baseline is not None:
        by_id = {r["id"]: r for r in baseline}
        both = [r for r in sorty if r["id"] in by_id]
        base_ok = sum(1 for r in both if by_id[r["id"]]["passed"])
        sorty_ok = sum(1 for r in both if r["outcome_ok"])
        hidden = [r for r in both if r["hidden_fact"]]
        lines.append("")
        lines.append("Same model, same rules, same pictures. The only difference is whether it may look again and ask:")
        lines.append("")
        lines.append("| Method | Correct bin and instruction | On the items whose answer is hidden |")
        lines.append("|---|---|---|")
        lines.append(f"| One-look camera (answers from the first picture) | {base_ok} of {len(both)} | "
                     f"{sum(1 for r in hidden if by_id[r['id']]['passed'])} of {len(hidden)} |")
        lines.append(f"| Sorty (looks again, asks, runs specialist checks) | {sorty_ok} of {len(both)} | "
                     f"{sum(1 for r in hidden if r['outcome_ok'])} of {len(hidden)} |")
    avg_t = sum(r["think_seconds"] for r in sorty) / max(n, 1)
    avg_req = sum(r["person_turns"] for r in sorty) / max(n, 1)
    zero = sum(1 for r in sorty if r["person_turns"] == 0)
    lines.append("")
    lines.append(f"Sorty's thinking time averaged {avg_t:.1f} s per item. It needed nothing from the person on {zero} of {n} items, "
                 f"and {avg_req:.1f} requests per item on average.")
    lines.append("")
    lines.append("## Every scenario")
    lines.append("")
    head = "| Scenario | What Sorty did | Final answer | Result |"
    lines += [head, "|---|---|---|---|"]
    if baseline is not None:
        lines[-2] = "| Scenario | What Sorty did | Final answer | Result | One-look camera |"
        lines[-1] = "|---|---|---|---|---|"
    for r in sorty:
        did = []
        for e in r["events"]:
            if e["event"] == "show":
                did.append(f"asked to {e['action'].replace('_', ' ')}")
            elif e["event"] == "ask":
                did.append(f"asked \"{e['question']}\"")
            elif e["event"] == "specialist":
                did.append(f"ran {e['check']} check")
        did_text = "; ".join(did) or "answered at once"
        result = "PASS" if r["passed"] else "FAIL: " + "; ".join(r["problems"])
        row = f"| {r['title']} | {did_text} | {summarise(r)} | {result} |"
        if baseline is not None:
            b = {x["id"]: x for x in baseline}.get(r["id"])
            if b is None:
                row += " |"
            else:
                row += f" {'ok' if b['passed'] else 'WRONG'}: {summarise(b)} |"
        lines.append(row.replace("\n", " "))
    if meta.get("skipped"):
        lines += ["", "## Skipped", "", "No image was available for: " + ", ".join(meta["skipped"]) + "."]
    lines += ["", "## How to read this", "",
              "- A scenario passes only if the bin is right, any needed instruction (such as pouring out liquid) is given, "
              "and Sorty behaved sensibly: asked when no camera could know, looked again when a camera could, and did not bother "
              "the person when the answer was already visible.",
              "- The one-look camera is graded on the bin and instruction only.",
              "- The pictures are Blender renders, not photos from a real bin camera. Real-camera behaviour still has to be checked on the device."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", default="", help="comma-separated scenario ids")
    ap.add_argument("--group", default="", help="only this group")
    ap.add_argument("--station", default="", help="station profile (default: from settings)")
    ap.add_argument("--baseline", action="store_true", help="also run the one-look comparison")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--model", default="")
    ap.add_argument("--effort", default="")
    ap.add_argument("--tag", default="latest", help="name for the result files")
    ap.add_argument("--verbose", action="store_true", help="print each conversation")
    ap.add_argument("--speed", default="", help="'fast' turns on fast mode")
    ap.add_argument("--no-prearm", action="store_true", help="no automatic check on a new view")
    args = ap.parse_args()

    if not has_api_key():
        print("No API key found. Put it in sorty/.env as ANTHROPIC_API_KEY=... and run again.")
        return 2

    settings = get_settings()
    if args.station:
        settings.station_id = args.station
    if args.model:
        settings.model = args.model
    if args.effort:
        settings.effort = args.effort
    if args.speed:
        settings.speed = args.speed
    if args.no_prearm:
        settings.prearm_specialist = False
    settings.api_retries = 6
    settings.request_timeout_s = 90.0
    station = load_station(settings.station_id)
    expect_key = "expect" if settings.station_id == "3bin" else f"expect_{settings.station_id}"

    bank = json.loads((ROOT / "tests" / "scenarios.json").read_text(encoding="utf-8"))["scenarios"]
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    chosen, skipped = [], []
    for sc in bank:
        if only and sc["id"] not in only:
            continue
        if args.group and sc.get("group") != args.group:
            continue
        if expect_key not in sc:
            continue
        if not all((IMAGES / f).exists() for f in sc["frames"].values()):
            skipped.append(sc["id"])
            continue
        chosen.append(sc)
    if not chosen:
        print("No runnable scenarios (are the images in tests/images yet?). Skipped:", ", ".join(skipped) or "none")
        return 2

    llm = LLM(settings)
    brain = Brain(settings, llm=llm, station=station)
    print(f"Running {len(chosen)} scenarios on {settings.model} (effort {settings.effort}), station {settings.station_id} ...", flush=True)

    def play(sc: dict) -> dict:
        try:
            rec = run_one(brain, llm, sc)
            transient = ("rate limited", "no connection", "API error 5")
            if rec["final"]["type"] == "error" and any(t in str(rec["final"].get("error", "")) for t in transient):
                time.sleep(30)                      # transient API trouble: try this scenario once more
                rec = run_one(brain, llm, sc)
        except Exception as exc:  # one broken scenario must not stop the run
            rec = {"id": sc["id"], "title": sc["title"], "group": sc.get("group", ""), "final": {"type": "error", "say": "", "error": f"{type(exc).__name__}: {exc}"},
                   "transcript": [], "person_turns": 0, "specialist_calls": 0, "model_calls": 0, "events": [], "think_seconds": 0, "wall_seconds": 0}
        expect = sc[expect_key]
        rec["problems"] = grade(expect, rec, station)
        rec["passed"] = not rec["problems"]
        rec["outcome_ok"] = not grade(expect, rec, station, behaviour=False)
        rec["hidden_fact"] = expect.get("needs") in ("ask", "view", "info")
        print(f"  {'PASS' if rec['passed'] else 'FAIL'}  {sc['id']:<24} {summarise(rec)[:90]}"
              + ("" if rec["passed"] else f"\n        -> {'; '.join(rec['problems'])}"), flush=True)
        if args.verbose:
            out = []
            for line in rec["transcript"]:
                if "person" in line:
                    out.append(f"        person: {line['person']}")
                else:
                    action = f" {line['action']}" if "action" in line else ""
                    out.append(f"        sorty [{line['sorty']}{action}]: {line['say']}")
            for e in rec["events"]:
                if e["event"] == "specialist":
                    out.append(f"        specialist {e['check']}: {json.dumps(e['result'], ensure_ascii=False)[:220]}")
            out.append(f"        ({rec['model_calls']} model calls, {rec['think_seconds']} s thinking)")
            print("\n".join(out), flush=True)
        return rec

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        sorty = list(pool.map(play, chosen))

    baseline = None
    if args.baseline:
        one_look = copy.copy(settings)
        one_look.max_person_turns = 0
        one_look.max_specialist_calls = 0
        base_brain = Brain(one_look, llm=llm, specialists={}, station=station)
        print("Running the one-look comparison ...", flush=True)

        def play_base(sc: dict) -> dict:
            try:
                rec = run_one(base_brain, llm, sc, interactive=False)
            except Exception as exc:
                rec = {"id": sc["id"], "title": sc["title"], "final": {"type": "error", "say": "", "error": str(exc)}, "events": [], "person_turns": 0,
                       "transcript": [], "think_seconds": 0}
            rec["problems"] = grade(sc[expect_key], rec, station, behaviour=False)
            rec["passed"] = not rec["problems"]
            return rec

        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            baseline = list(pool.map(play_base, chosen))

    cost = llm.usage.estimated_cost_usd(settings.model)
    meta = {"when": time.strftime("%Y-%m-%d %H:%M"), "model": settings.model, "effort": settings.effort,
            "station": settings.station_id, "cost_usd": cost, "usage": llm.usage.snapshot(), "skipped": skipped}
    RESULTS.mkdir(parents=True, exist_ok=True)
    slim = lambda rows: [{k: v for k, v in r.items() if k != "final"} | {"final_say": r["final"].get("say", ""), "final_type": r["final"]["type"],
                                                                         "verdict": r["final"].get("verdict")} for r in rows]
    (RESULTS / f"{args.tag}.json").write_text(json.dumps({"meta": meta, "sorty": slim(sorty), "baseline": slim(baseline) if baseline else None},
                                                         indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(RESULTS / ("REPORT.md" if args.tag == "latest" else f"REPORT_{args.tag}.md"), meta, sorty, baseline)

    passed = sum(1 for r in sorty if r["passed"])
    print(f"\nSorty: {passed} of {len(sorty)} scenarios passed.", end="")
    if baseline is not None:
        print(f"  One-look camera: {sum(1 for r in baseline if r['passed'])} of {len(baseline)} correct "
              f"(Sorty outcome-only: {sum(1 for r in sorty if r['outcome_ok'])}).", end="")
    print(f"\nEstimated API cost: ${cost:.2f}   tokens: {llm.usage.snapshot()}")
    if skipped:
        print("Skipped (no image yet):", ", ".join(skipped))
    return 0 if passed == len(sorty) else 1


if __name__ == "__main__":
    raise SystemExit(main())
