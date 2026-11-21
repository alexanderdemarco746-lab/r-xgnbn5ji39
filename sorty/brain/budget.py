"""A spending guard for the AI service.

Every AI call's cost is estimated from the token counts the API reports and
added to a small ledger file. Once the total reaches the limit, no further
live calls are made and the product drops back to practice mode.

The limit is SORTY_BUDGET_USD (default 5 dollars). The guard stops a little
before the limit, because the figure is an estimate. The hard guarantee is on
the account side: with auto-reload switched off in the Anthropic Console, a
prepaid balance cannot be overspent.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

LEDGER = Path(__file__).resolve().parent.parent / ".usage.json"
SAFETY_SHARE = 0.96            # stop at 96% of the limit: the ledger is an estimate

# USD per million tokens: (input, output, cached input read)
PRICES = {
    "claude-opus-5-5": (4.00, 20.00, 0.20),
    "claude-fable-5-2": (8.00, 40.00, 0.20),
    "claude-sonnet-5-5": (2.00, 10.00, 0.10),
    "claude-haiku-5-5": (0.10, 0.50, 0.01),
}
CACHE_WRITE_FACTOR = 1.25

_lock = threading.Lock()


class BudgetExceeded(RuntimeError):
    pass


def limit_usd() -> float:
    try:
        return float(os.environ.get("SORTY_BUDGET_USD", "5"))
    except ValueError:
        return 5.0


def cost_usd(model: str, usage) -> float:
    price_in, price_out, price_read = PRICES.get(model, PRICES["claude-opus-5-5"])
    get = lambda name: getattr(usage, name, 0) or 0
    total = (get("input_tokens") * price_in
             + get("output_tokens") * price_out
             + get("cache_read_input_tokens") * price_read
             + get("cache_creation_input_tokens") * price_in * CACHE_WRITE_FACTOR)
    return total / 1_000_000


def _read() -> dict:
    try:
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"spent_usd": 0.0, "calls": 0}


def spent_usd() -> float:
    return float(_read().get("spent_usd", 0.0))


def remaining_usd() -> float:
    return max(0.0, limit_usd() - spent_usd())


def exhausted() -> bool:
    return spent_usd() >= limit_usd() * SAFETY_SHARE


def check() -> None:
    """Call before every AI request."""
    if exhausted():
        raise BudgetExceeded(f"AI budget used up (about ${spent_usd():.2f} of ${limit_usd():.2f})")


def add(model: str, usage) -> float:
    """Record one finished AI request. Returns the new total."""
    if usage is None:
        return spent_usd()
    with _lock:
        data = _read()
        data["spent_usd"] = round(float(data.get("spent_usd", 0.0)) + cost_usd(model, usage), 6)
        data["calls"] = int(data.get("calls", 0)) + 1
        data["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        tmp = LEDGER.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps(data), encoding="utf-8")
            os.replace(tmp, LEDGER)
        except OSError:
            pass                                   # never let bookkeeping break an answer
        return data["spent_usd"]


def status() -> dict:
    spent = spent_usd()
    return {"limit_usd": limit_usd(), "spent_usd": round(spent, 2), "exhausted": exhausted()}
