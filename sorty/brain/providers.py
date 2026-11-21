"""Chat models for the LangGraph orchestrator: Claude or Gemini behind one interface.

The orchestrator (brain/graph_brain.py) only needs three things from a model:
call it with messages, let it call the tools, and read how many tokens it used.
This module builds that for either provider through the LangChain packages
(langchain-anthropic uses the official Anthropic SDK underneath;
langchain-google-genai uses Google's SDK).
"""
from __future__ import annotations

import copy
import os
from types import SimpleNamespace

from .config import Settings, load_dotenv

GOOGLE_KEY_NAMES = ("GEMINI_API_KEY", "GOOGLE_API_KEY")


def gemini_key() -> str:
    load_dotenv()
    for name in GOOGLE_KEY_NAMES:
        if os.environ.get(name):
            return os.environ[name]
    return ""


def has_gemini_key() -> bool:
    return bool(gemini_key())


def resolve(settings: Settings) -> tuple[str, str]:
    """Which provider and model id the current settings mean."""
    model = settings.model or ""
    wants_google = (getattr(settings, "provider", "") or "").lower() in ("google", "gemini") or model.startswith("gemini")
    if wants_google:
        return "google", (model if model.startswith("gemini") else getattr(settings, "gemini_model", "gemini-3.8-flash"))
    return "anthropic", model


def has_key_for(settings: Settings) -> bool:
    provider, _ = resolve(settings)
    if provider == "google":
        return has_gemini_key()
    load_dotenv()
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def make_chat_model(settings: Settings, model_id: str | None = None):
    """A LangChain chat model for the provider the settings point at."""
    provider, resolved = resolve(settings)
    model_id = model_id or resolved
    load_dotenv()
    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        key = gemini_key()
        if not key:
            raise RuntimeError("No Gemini API key found: put GEMINI_API_KEY=... in sorty/.env")
        kwargs = dict(model=model_id, google_api_key=key, timeout=settings.request_timeout_s, max_retries=settings.api_retries)
        effort = os.environ.get("SORTY_GEMINI_EFFORT", "")
        if effort:                                   # optional: low / medium / high thinking for Gemini
            kwargs["reasoning_effort"] = effort
        return ChatGoogleGenerativeAI(**kwargs)

    from langchain_anthropic import ChatAnthropic
    # Thinking is adaptive on current Claude models; depth is controlled with effort (low = fastest).
    return ChatAnthropic(
        model=model_id,
        max_tokens=16000,
        default_request_timeout=settings.request_timeout_s,
        max_retries=settings.api_retries,
        thinking={"type": "adaptive"},
        output_config={"effort": settings.effort},
    )


def _strip(node, drop=("additionalProperties", "strict")):
    """Remove JSON-schema keywords Gemini's function declarations do not accept."""
    if isinstance(node, dict):
        return {k: _strip(v, drop) for k, v in node.items() if k not in drop}
    if isinstance(node, list):
        return [_strip(v, drop) for v in node]
    return node


def tools_for(tools: list[dict], provider: str) -> list[dict]:
    """The brain's tool list (written in Claude's format) in the form each provider's bind_tools takes."""
    if provider == "google":
        return [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                                  "parameters": _strip(copy.deepcopy(t["input_schema"]))}} for t in tools]
    return tools            # Claude: strict schemas pass through unchanged


def bind(model, tools: list[dict], provider: str):
    """The model with the tools attached; at most one tool call per turn where the provider can enforce it."""
    if provider == "google":
        return model.bind_tools(tools_for(tools, provider))
    return model.bind_tools(tools_for(tools, provider), tool_choice="auto", parallel_tool_calls=False)


def usage_of(message) -> SimpleNamespace:
    """Token counts of one reply, in the shape brain/budget.py and brain/llm.Usage expect.

    LangChain reports input_tokens as the total including cached tokens, with the
    cached parts listed separately; split them back apart so each is priced correctly.
    """
    meta = getattr(message, "usage_metadata", None) or {}
    details = meta.get("input_token_details") or {}
    read = int(details.get("cache_read", 0) or 0)
    # The Anthropic package moves cache writes to these two keys (and zeroes "cache_creation")
    # whenever the API reports them per lifetime; add all three so none is missed.
    write = sum(int(details.get(k, 0) or 0) for k in ("cache_creation", "ephemeral_5m_input_tokens", "ephemeral_1h_input_tokens"))
    total_in = int(meta.get("input_tokens", 0) or 0)
    return SimpleNamespace(
        input_tokens=max(0, total_in - read - write),
        output_tokens=int(meta.get("output_tokens", 0) or 0),
        cache_read_input_tokens=read,
        cache_creation_input_tokens=write,
    )


def text_of(message) -> str:
    """The plain text of a reply, whichever way the provider packs it."""
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    parts = []
    for block in content or []:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts)


def stop_reason(message) -> str:
    meta = getattr(message, "response_metadata", None) or {}
    return str(meta.get("stop_reason") or meta.get("finish_reason") or "")
