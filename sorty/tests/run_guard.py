"""Measure the instant alert on every test picture.

    python -m tests.run_guard              (from the sorty folder, needs the API key)
    python -m tests.run_guard --repeat 3   (each picture three times)

Each picture is shown to the fast guard alone. Pictures of load-wreckers must
raise an alert with the right category; every other picture must stay silent.
Writes tests/results/GUARD.md and guard.json.
"""
from __future__ import annotations

import argparse
import base64
import json
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from brain import budget, get_settings, load_station  # noqa: E402
from brain.guard import LoadGuard  # noqa: E402

IMAGES = ROOT / "tests" / "images"
RESULTS = ROOT / "tests" / "results"

# Pictures that show a load-wrecker, and the category the guard must name. Everything else must stay silent.
WRECKER_PICTURES = {
    "battery_aa.jpg": "battery",
    "smartphone.jpg": "electronics",
    "vape.jpg": "vape",
    "plastic_bag.jpg": "plastic_bag",
    "tied_bag.jpg": "bagged_trash",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--model", default="")
    args = ap.parse_args()

    settings = get_settings()
    if args.model:
        settings.guard_model = args.model
    guard = LoadGuard(settings, load_station(settings.station_id))
    spent_before = budget.spent_usd()
    pictures = sorted(p for p in IMAGES.glob("*.jpg"))
    jobs = [(p, n) for p in pictures for n in range(args.repeat)]

    def one(job):
        path, _ = job
        look = guard.look(base64.b64encode(path.read_bytes()).decode("ascii"))
        return path.name, look

    guard.look(base64.b64encode(pictures[0].read_bytes()).decode("ascii"))     # warm-up: the first call opens the connection
    t0 = time.monotonic()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        looks = list(pool.map(one, jobs))
    wall = time.monotonic() - t0

    rows, caught, wreckers, false_alarms, ordinary, errors, times = [], 0, 0, 0, 0, 0, []
    for name, look in looks:
        want = WRECKER_PICTURES.get(name)
        if "error" in look:
            errors += 1
            rows.append((name, want or "-", "ERROR " + look["error"], "", look["ms"], "error"))
            continue
        times.append(look["ms"])
        said = look["category"] if look["alert"] else "(silent)"
        if want:
            wreckers += 1
            ok = look["alert"] and look["category"] == want
            caught += ok
            result = "caught" if ok else ("wrong kind" if look["alert"] else "MISSED")
        else:
            ordinary += 1
            false_alarms += bool(look["alert"])
            result = "FALSE ALARM" if look["alert"] else "silent, correct"
        rows.append((name, want or "-", said, look.get("item", ""), look["ms"], result))

    times.sort()
    median = statistics.median(times) if times else 0
    slowest = times[-1] if times else 0
    cost = budget.spent_usd() - spent_before
    summary = {
        "model": guard.model, "pictures": len(pictures), "repeat": args.repeat,
        "wreckers_shown": wreckers, "wreckers_caught": caught,
        "ordinary_shown": ordinary, "false_alarms": false_alarms, "errors": errors,
        "median_ms": int(median), "slowest_ms": int(slowest), "cost_usd": round(cost, 4),
        "when": time.strftime("%Y-%m-%d %H:%M"),
    }

    lines = [
        "# Instant alert test report", "",
        f"Run: {summary['when']}  |  fast model: `{guard.model}`  |  picture size: {settings.guard_image_px} px  |  "
        f"pictures: Blender renders in `tests/images`  |  estimated API cost of this run: ${cost:.3f}", "",
        "## Result", "",
        "| What was shown | Result |", "|---|---|",
        f"| Load-wreckers (battery, phone, vape, plastic bag, bag of trash) | alert raised on **{caught} of {wreckers}** |",
        f"| Ordinary items (bottles, cans, boxes, cups, food and so on) | false alarm on **{false_alarms} of {ordinary}** |",
        f"| Time for one fast look | typically **{median / 1000:.1f} s**, slowest {slowest / 1000:.1f} s |", "",
        "The fast look ran on its own here, several pictures at a time. In the product it runs beside the careful model, "
        "and only an alert it is sure about is shown; when it stays silent the careful model answers as usual.", "",
        "## Every picture", "",
        "| Picture | Should alert as | Fast model said | It saw | Time | Result |", "|---|---|---|---|---|---|",
    ]
    for name, want, said, item, ms, result in rows:
        lines.append(f"| {name} | {want} | {said} | {item} | {ms / 1000:.1f} s | {result} |")
    lines += ["", "## How to read this", "",
              "- The pictures are Blender renders, not photos from a real bin camera, and each load-wrecker has only one picture.",
              "- A missed alert is not a wrong answer: the careful model still sends the item to the right place, a few seconds later.",
              "- A false alarm would be a wrong answer, which is why the fast model is told to stay silent unless it is sure."]
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "GUARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RESULTS / "guard.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=1), encoding="utf-8")

    for name, want, said, item, ms, result in rows:
        print(f"{result:16} {name:28} want={want:13} said={said:13} {ms:5} ms  {item}")
    print(json.dumps(summary))
    print(f"wall time {wall:.1f} s")


if __name__ == "__main__":
    main()
