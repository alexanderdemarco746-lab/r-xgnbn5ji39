"""One place for every Claude call: model options, refusal fallback, usage.

Uses the official Anthropic SDK. Thinking is adaptive on current models and
depth is controlled with effort; forced tool choice is not available on
Claude Opus 5.5, so callers use tool_choice "auto" with strict schemas.
"""
from __future__ import annotations

import threading

import anthropic

from . import budget
from .config import Settings

FALLBACK_BETA = "server-side-fallback-2026-07-01"

# USD per million tokens (input, output). Only used to estimate test spend.
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-fable-5-2": (8.00, 40.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}


def supports_fallbacks(model: str) -> bool:
    return model.startswith(("claude-opus-5", "claude-fable-5", "claude-mythos-5", "claude-sonnet-5-5"))


class Usage:
    """Thread-safe token counters."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.calls = 0
        self.input = 0
        self.output = 0
        self.cache_read = 0
        self.cache_write = 0

    def add(self, usage) -> None:
        if usage is None:
            return
        with self._lock:
            self.calls += 1
            self.input += getattr(usage, "input_tokens", 0) or 0
            self.output += getattr(usage, "output_tokens", 0) or 0
            self.cache_read += getattr(usage, "cache_read_input_tokens", 0) or 0
            self.cache_write += getattr(usage, "cache_creation_input_tokens", 0) or 0

    def snapshot(self) -> dict:
        with self._lock:
            return {"calls": self.calls, "input": self.input, "output": self.output,
                    "cache_read": self.cache_read, "cache_write": self.cache_write}

    def estimated_cost_usd(self, model: str) -> float:
        price_in, price_out = PRICES.get(model, PRICES["claude-opus-5-5"])
        s = self.snapshot()
        cost = (s["input"] * price_in + s["output"] * price_out
                + s["cache_read"] * price_in * 0.05 + s["cache_write"] * price_in * 1.25)
        return round(cost / 1_000_000, 4)


class LLM:
    def __init__(self, settings: Settings, client: anthropic.Anthropic | None = None) -> None:
        self.settings = settings
        # Credentials come from the environment (ANTHROPIC_API_KEY, loaded from .env).
        self.client = client or anthropic.Anthropic(timeout=settings.request_timeout_s, max_retries=settings.api_retries)
        self._fallbacks = settings.use_fallbacks
        self.guard_budget = client is None        # a stand-in client (tests) spends nothing and is not tracked
        self.usage = Usage()

    def create(self, *, model: str, effort: str, output_config: dict | None = None, **kwargs):
        params = dict(
            model=model,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            output_config={"effort": effort, **(output_config or {})},
            **kwargs,
        )
        if self.settings.speed == "fast":
            params["speed"] = "fast"
        if self.guard_budget:
            budget.check()                       # raises BudgetExceeded once the spending limit is reached

        if self._fallbacks and supports_fallbacks(model):
            try:
                # If a safety classifier declines a request, the API re-runs it on
                # Anthropic's recommended fallback model inside the same call.
                resp = self.client.beta.messages.create(betas=[FALLBACK_BETA], fallbacks="default", **params)
            except anthropic.BadRequestError as exc:
                text = str(exc).lower()
                if "fallback" not in text and "beta" not in text:
                    raise
                self._fallbacks = False          # not available for this account: carry on without
                resp = self.client.beta.messages.create(**params)
        else:
            resp = self.client.beta.messages.create(**params)
        self.usage.add(getattr(resp, "usage", None))
        if self.guard_budget:
            budget.add(model, getattr(resp, "usage", None))
        return resp


def first_text(resp) -> str:
    for block in resp.content:
        if block.type == "text":
            return block.text
    return ""
