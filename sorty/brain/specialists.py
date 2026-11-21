"""Specialist vision checks the brain can query.

A specialist is anything with a `name` and a `run(frame_bytes, focus) -> dict`
method. The two built in here are focused inspection passes: they get the
frame at full resolution plus a sharpened centre crop, a fixed rubric, and
must answer in a fixed measurement schema.

To plug in a trained detector (for example a YOLO grease model running on the
bin's own computer), write a class with the same two members and register it:

    brain.specialists["contamination"] = MyGreaseDetector()

The brain does not care how the measurement is produced.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Protocol

from . import prompts
from .config import Settings
from .imaging import inspection_views, to_block
from .llm import LLM, first_text


class Specialist(Protocol):
    name: str

    def run(self, frame: bytes, focus: str) -> dict: ...


class ClaudeInspector:
    """A focused inspection pass with its own rubric and output schema."""

    def __init__(self, llm: LLM, settings: Settings, name: str, system: str, schema: dict) -> None:
        self.llm = llm
        self.settings = settings
        self.name = name
        self.system = system
        self.schema = schema

    def run(self, frame: bytes, focus: str) -> dict:
        views = inspection_views(frame, self.settings.specialist_image_px)
        content = [to_block(v) for v in views]
        content.append({"type": "text", "text": f"Where to look and what to settle: {focus or 'the item being presented'}"})
        resp = self.llm.create(
            model=self.settings.specialist_model_id,
            effort=self.settings.specialist_effort,
            system=self.system,
            messages=[{"role": "user", "content": content}],
            output_config={"format": {"type": "json_schema", "schema": self.schema}},
        )
        if resp.stop_reason in ("refusal", "max_tokens"):
            return {"error": f"check unavailable ({resp.stop_reason})"}
        try:
            return json.loads(first_text(resp))
        except json.JSONDecodeError:
            return {"error": "check returned unreadable output"}


def build_specialists(llm: LLM, settings: Settings) -> dict[str, Specialist]:
    return {
        "contamination": ClaudeInspector(llm, settings, "contamination",
                                         prompts.CONTAMINATION_SYSTEM, prompts.CONTAMINATION_SCHEMA),
        "label": ClaudeInspector(llm, settings, "label",
                                 prompts.LABEL_SYSTEM, prompts.LABEL_SCHEMA),
    }


def run_checks(specialists: dict[str, Specialist], checks: list[str], frame: bytes, focus: str) -> dict[str, dict]:
    """Run several checks on one frame at the same time."""
    wanted = [c for c in dict.fromkeys(checks) if c in specialists]
    if not wanted:
        return {}

    def one(name: str) -> tuple[str, dict]:
        try:
            return name, specialists[name].run(frame, focus)
        except Exception as exc:  # a failed check must never take the kiosk down
            return name, {"error": f"check failed: {type(exc).__name__}"}

    if len(wanted) == 1:
        return dict([one(wanted[0])])
    with ThreadPoolExecutor(max_workers=len(wanted)) as pool:
        return dict(pool.map(one, wanted))


def summarize(name: str, result: dict) -> str:
    """One readable line for the decision trace."""
    if "error" in result:
        return f"{name}: {result['error']}"
    if name == "contamination":
        if result.get("surface_visible") == "no":
            return "contamination: surface not visible in this frame"
        return (f"contamination: {result.get('severity', '?')}, about {result.get('coverage_percent', '?')}% "
                f"of {result.get('surface_inspected', 'surface')} ({result.get('confidence', '?')} confidence)")
    if name == "label":
        found = ", ".join(result.get("text_found") or []) or "no readable text"
        return (f"label: {found}; resin code {result.get('resin_code', '?')}; "
                f"compostable mark {result.get('compostable_marking', '?')} ({result.get('confidence', '?')} confidence)")
    return f"{name}: {json.dumps(result)[:160]}"
