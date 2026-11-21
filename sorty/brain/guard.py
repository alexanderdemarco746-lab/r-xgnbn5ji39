"""The instant alert: a fast second model that watches for load-wreckers.

A few items do far more damage than an ordinary sorting mistake. A battery or a
vape can set a recycling truck or a sorting plant on fire, a plastic bag wraps
around the sorting machines and stops the line, a bag of trash spoils what is
around it. For these, a fast warning matters more than a nuanced answer.

So the moment the station activates, two models start at the same time on the
same camera frame:

  - the careful brain (agent.py or graph_brain.py), which may look again, ask
    the person and run specialist checks, and
  - this guard: one small picture, one narrow question, the fastest model.

When the guard is sure, the person hears "Stop!" without waiting for the
careful brain. When it is not sure it stays silent and the careful brain
answers as usual, so the guard can only make Sorty faster, never less careful.

The detector is pluggable: anything with `detect(frame_bytes) -> dict` works, so
a small model running on the bin's own computer can take the place of the cloud
call (see ClaudeDetector for the shape of the answer).
"""
from __future__ import annotations

import json
import secrets
import time

import anthropic

from . import phrases
from .config import Settings
from .imaging import decode_frame, main_view, to_block
from .llm import LLM, first_text

# What each load-wrecker does and where it goes instead. "to" is a bin id on the
# station, or "special" with a key into the station's special_destinations.
WRECKERS = {
    "battery": {
        "harm": "fire", "to": "special", "dest": "battery",
        "name": {"en": "Battery", "es": "Pila"},
        "why": {"en": "Batteries start fires in recycling trucks.",
                "es": "Las pilas causan incendios en los camiones."},
    },
    "vape": {
        "harm": "fire", "to": "special", "dest": "battery",
        "name": {"en": "Vape", "es": "Vapeador"},
        "why": {"en": "Vapes hide a battery that starts fires.",
                "es": "Los vapeadores esconden una pila que causa incendios."},
    },
    "electronics": {
        "harm": "fire", "to": "special", "dest": "ewaste",
        "name": {"en": "Electronics", "es": "Aparato electrónico"},
        "why": {"en": "Electronics hide batteries that start fires.",
                "es": "Los aparatos esconden pilas que causan incendios."},
    },
    "plastic_bag": {
        "harm": "jam", "to": "landfill",
        "name": {"en": "Plastic bag", "es": "Bolsa de plástico"},
        "why": {"en": "Plastic bags jam the sorting machines.",
                "es": "Las bolsas atascan las máquinas de reciclaje."},
    },
    "bagged_trash": {
        "harm": "spoil", "to": "landfill",
        "name": {"en": "Bag of trash", "es": "Bolsa de basura"},
        "why": {"en": "Bagged trash spoils the whole recycling load.",
                "es": "La basura en bolsa arruina todo el reciclaje."},
    },
    "sharp": {
        "harm": "injury", "to": "special", "dest": "sharps",
        "name": {"en": "Needle", "es": "Aguja"},
        "why": {"en": "Needles injure the people who sort.",
                "es": "Las agujas hieren a quienes separan."},
    },
    "gas_canister": {
        "harm": "blast", "to": "special", "dest": "hazardous",
        "name": {"en": "Gas canister", "es": "Cartucho de gas"},
        "why": {"en": "Gas canisters can explode in the truck.",
                "es": "Los cartuchos de gas pueden explotar en el camión."},
    },
}

STOP = {"en": "Stop!", "es": "¡Alto!"}
STOP_LABEL = {"en": "Stop", "es": "Alto"}
NOT_IN_BIN = {"en": "Not in the {color} bin.", "es": "No va en el contenedor {color}."}
PLEASE_USE = {"en": "Please use {dest}.", "es": "Por favor usa {dest}."}

GUARD_SYSTEM = """You are the instant safety check of a waste-sorting station. A camera shows what a person is holding up to throw away. A slower, careful check runs at the same time and gives the full answer. Your only job is to spot, at a glance, the few things that wreck a whole load of recycling or endanger the trucks, the sorting plant and the people who work there.

Judge only the one thing being held up or placed in front of the camera. Ignore the person, what they wear or carry (a watch, earbuds, a phone in a pocket or in the other hand) and the room.

Categories:
- battery: loose batteries of any size or shape, battery packs, power banks.
- vape: e-cigarettes, vape pens and pods. They hide a lithium battery.
- electronics: phones, tablets, laptops, earbuds, chargers, cables, and anything else with a battery or a cord.
- plastic_bag: an empty or loose plastic bag, plastic film or wrap, such as a shopping bag, a bread bag, bubble wrap or cling film. Chip bags, candy wrappers and pouches do not count.
- bagged_trash: a tied or stuffed bag with trash inside.
- sharp: needles, syringes, razor blades.
- gas_canister: propane or camping-gas canisters, lighters.
- none: everything else, including bottles, cans, spray cans, cups, boxes, cartons, paper, food, wrappers and chip bags, and frames where nothing is being presented.

Answer sure "yes" only when the picture makes the category plain. If you hesitate between a category and "none", give your best category with sure "no": staying quiet is safe, because the careful check still answers. A false alarm is worse than a missed one."""

GUARD_SCHEMA = {
    "type": "object",
    "properties": {
        "item": {"type": "string", "description": "The thing being presented, in two to four everyday words"},
        "category": {"type": "string", "enum": list(WRECKERS) + ["none"]},
        "sure": {"type": "string", "enum": ["yes", "no"]},
    },
    "required": ["item", "category", "sure"],
    "additionalProperties": False,
}


class ClaudeDetector:
    """The fast check as one small Claude call: a small picture, no deliberate thinking, a fixed answer shape."""

    def __init__(self, llm: LLM, settings: Settings) -> None:
        self.llm = llm
        self.s = settings
        self.model = settings.guard_model
        self._plain = True              # first try without thinking: a glance does not need it

    def detect(self, frame: bytes) -> dict:
        view = main_view(frame, self.s.guard_image_px)
        request = dict(
            model=self.model, effort="low", system=GUARD_SYSTEM,
            messages=[{"role": "user", "content": [to_block(view), {"type": "text", "text": "What is being held up?"}]}],
            output_config={"format": {"type": "json_schema", "schema": GUARD_SCHEMA}},
        )
        if self._plain:
            try:
                resp = self.llm.create(thinking={"type": "disabled"}, max_tokens=300, **request)
            except anthropic.BadRequestError:
                self._plain = False     # this model insists on its own thinking setting: use the default
                resp = self.llm.create(**request)
        else:
            resp = self.llm.create(**request)
        return json.loads(first_text(resp))


class LoadGuard:
    def __init__(self, settings: Settings, station: dict, llm: LLM | None = None, detector=None) -> None:
        self.s = settings
        self.station = station
        self.detector = detector or ClaudeDetector(llm or LLM(settings), settings)
        self.model = getattr(self.detector, "model", "on-device detector")

    def look(self, image_b64: str) -> dict:
        """One fast look at a camera frame. Never raises.

        Returns {"alert": bool, "category", "item", "sure", "ms"}; on a failure
        {"alert": False, "error", "ms"}. An alert needs a known category and a sure answer.
        """
        t0 = time.monotonic()
        try:
            found = self.detector.detect(decode_frame(image_b64))
            category, sure = str(found.get("category", "none")), str(found.get("sure", "no"))
            item = str(found.get("item", "")).strip()[:60]
        except Exception as exc:                      # a failed glance must never hold up the careful answer
            return {"alert": False, "error": type(exc).__name__, "ms": int((time.monotonic() - t0) * 1000)}
        return {"alert": category in WRECKERS and sure == "yes", "category": category, "item": item,
                "sure": sure, "ms": int((time.monotonic() - t0) * 1000)}


def alert_turn(station: dict, category: str, item: str, lang: str, ms: int, source: str) -> dict:
    """The Turn the kiosk shows for an alert: an ordinary verdict plus an `alert` block."""
    w = WRECKERS[category]
    lk = lang if lang in STOP else "en"
    tr = phrases.t(lk)
    bins = {b["id"]: b for b in station["bins"]}
    why = w["why"][lk]
    item = phrases.cap(item.strip()) or w["name"][lk]
    avoid = bins.get("recycle")
    target = bins.get(w["to"]) if w["to"] != "special" else None

    if target is not None:
        where = phrases.cap(phrases.bin_phrase(target, lk))
        steps = [{"kind": "bin", "item": item, "bin": target["id"], "position": target["position"], "text": where}]
        lead = ""
        if avoid is not None and avoid["id"] != target["id"]:
            lead = NOT_IN_BIN[lk].format(color=avoid["color_name"].get(lk, avoid["color_name"]["en"]))
        spoken = [STOP[lk], lead, why, where + ".", tr["thanks"]]
        headline, primary, dest = where, target["id"], None
    else:
        named = station.get("special_destinations", {}).get(w.get("dest", ""), {})
        dest = named.get(lk) or named.get("en") or tr["default_dest"]
        steps = [{"kind": "special", "item": item, "text": tr["special_headline"], "dest": phrases.cap(dest)}]
        spoken = [STOP[lk], tr["special_headline"] + ".", why, PLEASE_USE[lk].format(dest=dest), tr["thanks"]]
        headline, primary = tr["special_headline"], "special"

    seconds = f"{ms / 1000:.1f} s"
    trace = [
        {"t_ms": 0, "kind": "frame", "text": "Item presented to the camera"},
        {"t_ms": ms, "kind": "alert", "text": f'Instant alert ({source}, {seconds}): "{item}" can wreck a whole load '
                                              f'({w["harm"]}). Answered without waiting for the careful check'},
        {"t_ms": ms, "kind": "verdict", "text": f"{item} -> {primary}. {why}"},
    ]
    return {
        "session_id": "g_" + secrets.token_hex(4),
        "turn": 1,
        "type": "verdict",
        "say": " ".join(part for part in spoken if part),
        "display": {"headline": headline, "sub": why, "item_label": item, "icon": "warning"},
        "verdict": {"primary_bin": primary, "steps": steps, "reason": why,
                    "special_dest": phrases.cap(dest) if dest else None, "confidence": "high"},
        "alert": {"category": category, "harm": w["harm"], "label": STOP_LABEL[lk], "why": why,
                  "avoid_bin": avoid["id"] if avoid is not None else None, "ms": ms, "source": source},
        "trace": trace,
        "timing_ms": ms,
    }
