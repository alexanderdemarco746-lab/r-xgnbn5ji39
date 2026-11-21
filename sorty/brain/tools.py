"""The four moves Sorty can make, plus "nothing to sort", as Claude tools.

Schemas are strict (every field required, no extra fields) so tool inputs
always validate. The bin enum comes from the station profile.
"""
from __future__ import annotations

VIEW_ACTIONS = [
    "open_show_inside",   # open the box/container/lid and show the inside
    "flip_over",          # turn it around to show the other side
    "show_bottom",        # show the underside (material marks live there)
    "show_label",         # turn the label or printed text toward the camera
    "hold_closer",        # bring it closer to the camera
    "one_at_a_time",      # several things at once: show one
    "hold_still",         # blurred or dark frame
]

SPECIALIST_CHECKS = ["contamination", "label"]


def _obj(properties: dict) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties.keys()),
        "additionalProperties": False,
    }


def build_tools(station: dict) -> list[dict]:
    bin_ids = [b["id"] for b in station["bins"]] + ["special", "not_trash"]
    return [
        {
            "name": "request_new_view",
            "description": (
                "Ask the person to move, open or turn the item so the camera can see a deciding "
                "detail, then receive a fresh camera frame. For facts a camera CAN see, just not "
                "from the current view. Counts as one request to the person."
            ),
            "strict": True,
            "input_schema": _obj({
                "action": {"type": "string", "enum": VIEW_ACTIONS},
                "say": {"type": "string", "description": "Exact words to speak. Start with the verb, at most eight words."},
                "because": {"type": "string", "description": "Shown under the instruction: at most six plain words on why, e.g. 'I can't see the inside.'"},
                "item_seen": {"type": "string", "description": "What you see so far, one to three words, e.g. 'Pizza box'"},
                "then_check": {
                    "type": "string",
                    "enum": ["none"] + SPECIALIST_CHECKS,
                    "description": (
                        "A specialist check to run on the new frame before it reaches you, when you "
                        "already know the new view will need a precise read: 'contamination' when "
                        "the question is grease or food, 'label' when it is small print or a material "
                        "mark. Otherwise 'none'."
                    ),
                },
            }),
        },
        {
            "name": "ask_person",
            "description": (
                "Ask the person one short question about a fact that no camera can see (liquid in an "
                "opaque container, contents of a tied bag, whether a spray can is empty). Counts as "
                "one request to the person."
            ),
            "strict": True,
            "input_schema": _obj({
                "question": {"type": "string", "description": "Exact words to speak, at most eight words."},
                "kind": {"type": "string", "enum": ["yes_no", "choice"]},
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "For kind 'choice': two or three short answer options. Empty for yes_no.",
                },
                "because": {"type": "string", "description": "Shown under the question: at most six plain words on why you ask, e.g. 'I can't see inside the can.'"},
                "item_seen": {"type": "string", "description": "What you see, one to three words, e.g. 'Soda can'"},
                "fact": {"type": "string", "description": "The unknown fact in two or three words, e.g. 'liquid inside'"},
            }),
        },
        {
            "name": "run_specialist",
            "description": (
                "Run dedicated vision checks on the current camera frame at full resolution and get "
                "their measurements back. 'contamination' measures food, grease and liquid on a "
                "surface. 'label' reads material marks, resin codes, compostable marks and small "
                "print. Use when the detail is in view but too subtle to call with confidence. "
                "Does not involve the person."
            ),
            "strict": True,
            "input_schema": _obj({
                "checks": {"type": "array", "items": {"type": "string", "enum": SPECIALIST_CHECKS}},
                "focus": {"type": "string", "description": "Which part to examine and the question to settle."},
            }),
        },
        {
            "name": "give_verdict",
            "description": "Tell the person where the item goes. Ends the interaction.",
            "strict": True,
            "input_schema": _obj({
                "items": {
                    "type": "array",
                    "description": "One entry per item or part, most important first, at most two.",
                    "items": _obj({
                        "item": {"type": "string", "description": "Plain name, one to three words, e.g. 'Greasy pizza box'"},
                        "bin": {"type": "string", "enum": bin_ids},
                        "prep": {"type": "string", "description": "What to do before binning, verb first, at most six words. Empty string when nothing."},
                        "special_dest": {"type": "string", "description": "Where it goes when bin is 'special', e.g. 'the battery drop-off'. Empty string otherwise."},
                    }),
                },
                "reason": {"type": "string", "description": "One short friendly sentence teaching the rule, at most ten words."},
                "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            }),
        },
        {
            "name": "nothing_to_sort",
            "description": "The frame shows no item to sort (empty view, only a person or hand, a passer-by). Ends the interaction quietly.",
            "strict": True,
            "input_schema": _obj({
                "what_i_see": {"type": "string", "description": "Brief note of what is in the frame."},
                "say": {"type": "string", "description": "A short friendly prompt, e.g. 'Hold your item up to the camera.'"},
            }),
        },
    ]
