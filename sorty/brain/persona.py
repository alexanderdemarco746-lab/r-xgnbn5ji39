"""A simulated person, for the scenario tests and the hands-free demo.

Given the hidden facts of a scenario ("the can is still half full") and what
Sorty just said, it replies the way a person at the bin would.
"""
from __future__ import annotations

from . import prompts
from .config import Settings
from .llm import LLM, first_text


def simulated_answer(llm: LLM, settings: Settings, facts: str, said: str, lang: str = "en") -> str:
    language = prompts.LANGUAGE_NAMES.get(lang, "English")
    resp = llm.create(
        model=settings.model,
        effort="low",
        system=prompts.PERSONA_SYSTEM,
        messages=[{"role": "user", "content": (
            f"Facts about you and what you are holding:\n{facts}\n\n"
            f'The assistant said: "{said}"\n\n'
            f"Reply in {language}, spoken words only."
        )}],
    )
    text = first_text(resp).strip().strip('"')
    return text or "not sure"
