"""Settings for Sorty: environment, model choice, station profile.

Everything a deployment may want to change lives here or in the station
profile JSON (brain/rules/station_<id>.json), so the same brain can be
mounted on any bin station.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # .../sorty
RULES_DIR = Path(__file__).resolve().parent / "rules"


def load_dotenv(path: Path | None = None) -> None:
    """Minimal .env reader (KEY=VALUE per line). Real environment wins."""
    path = path or ROOT / ".env"
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and value and not os.environ.get(key):
            os.environ[key] = value


@dataclass
class Settings:
    model: str = "claude-opus-5-5"
    effort: str = "low"                 # main loop: latency matters at a bin
    specialist_model: str = ""          # empty -> same as model
    specialist_effort: str = "medium"   # inspection passes favour precision
    speed: str = ""                     # "fast" enables fast mode (costs more)
    use_fallbacks: bool = True          # server-side refusal fallback
    station_id: str = "3bin"
    port: int = 8787
    request_timeout_s: float = 45.0
    # Interaction budget: people give a bin about ten seconds of patience.
    max_person_turns: int = 3           # questions + "show me again" combined
    max_specialist_calls: int = 3
    max_model_calls: int = 10
    main_image_px: int = 1024           # long edge sent to the main loop
    specialist_image_px: int = 1600     # long edge sent to specialists
    answer_timeout_s: int = 12
    show_timeout_s: int = 10
    verdict_hold_s: int = 8
    save_frames: bool = False           # debugging only; off = nothing stored
    assistant_name: str = "Sorty"
    languages: list[str] = field(default_factory=lambda: ["en", "es"])

    @property
    def specialist_model_id(self) -> str:
        return self.specialist_model or self.model


def get_settings() -> Settings:
    load_dotenv()
    env = os.environ.get
    s = Settings()
    s.model = env("SORTY_MODEL", s.model)
    s.effort = env("SORTY_EFFORT", s.effort)
    s.specialist_model = env("SORTY_SPECIALIST_MODEL", s.specialist_model)
    s.specialist_effort = env("SORTY_SPECIALIST_EFFORT", s.specialist_effort)
    s.speed = env("SORTY_SPEED", s.speed)
    s.use_fallbacks = env("SORTY_FALLBACKS", "1") not in ("0", "false", "no")
    s.station_id = env("SORTY_STATION", s.station_id)
    s.port = int(env("SORTY_PORT", str(s.port)))
    s.max_person_turns = int(env("SORTY_MAX_PERSON_TURNS", str(s.max_person_turns)))
    s.save_frames = env("SORTY_SAVE_FRAMES", "0") in ("1", "true", "yes")
    return s


def has_api_key() -> bool:
    load_dotenv()
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def load_station(station_id: str) -> dict:
    path = RULES_DIR / f"station_{station_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"No station profile {path.name} in {RULES_DIR}")
    station = json.loads(path.read_text(encoding="utf-8"))
    ids = [b["id"] for b in station["bins"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Station profile has duplicate bin ids")
    return station
