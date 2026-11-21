"""Fixed wording for what Sorty says and shows.

Verdicts always use the same sentence frame ("Blue bin, on your left.") so
people learn it after one use: colour first (fastest cue), then position
(matches the arrow and the lit bin), then a short reason.
"""
from __future__ import annotations

T = {
    "en": {
        "position": {"left": "on your left", "center": "in the middle", "right": "on your right"},
        "bin": "{color} bin, {position}",
        "first_then": "First, {prep}. Then: {bin}.",
        "single": "{bin}.",
        "item_bin": "{item}: {bin}.",
        "special": "Not in these bins. Please use {dest}.",
        "special_headline": "Not in these bins",
        "keep": "That doesn't look like trash.",
        "thanks": "Thank you!",
        "error_say": "I can't tell right now. Please check the labels on the bins.",
        "error_headline": "Please check the bin labels",
        "no_item": "Hold your item up to the camera.",
        "yes": "Yes", "no": "No", "unsure": "Not sure",
        "default_dest": "a special drop-off",
    },
    "es": {
        "position": {"left": "a tu izquierda", "center": "en el centro", "right": "a tu derecha"},
        "bin": "contenedor {color}, {position}",
        "first_then": "Primero, {prep}. Luego: {bin}.",
        "single": "{bin}.",
        "item_bin": "{item}: {bin}.",
        "special": "No va en estos contenedores. Por favor usa {dest}.",
        "special_headline": "No va en estos contenedores",
        "keep": "Eso no parece basura.",
        "thanks": "¡Gracias!",
        "error_say": "Ahora no puedo ver bien. Por favor revisa las etiquetas.",
        "error_headline": "Revisa las etiquetas",
        "no_item": "Acerca tu objeto a la cámara.",
        "yes": "Sí", "no": "No", "unsure": "No sé",
        "default_dest": "un punto especial",
    },
}

ACTION_ICONS = {
    "open_show_inside": "open",
    "flip_over": "flip",
    "show_bottom": "bottom",
    "show_label": "label",
    "hold_closer": "closer",
    "one_at_a_time": "separate",
    "hold_still": "still",
}


def t(lang: str) -> dict:
    return T.get(lang, T["en"])


def cap(text: str) -> str:
    text = text.strip()
    return text[:1].upper() + text[1:] if text else text


def lower_first(text: str) -> str:
    text = text.strip().rstrip(".!")
    if len(text) > 1 and text[1].isupper():      # acronym such as "PLA cup"
        return text
    return text[:1].lower() + text[1:] if text else text


def clean_prep(text: str) -> str:
    """One short action. The verdict sentence adds "First, ... Then: ..." itself, so drop those words here."""
    import re
    text = text.strip().rstrip(".!")
    # keep only the first action: "pour it out, then rinse" -> "pour it out"
    text = re.split(r"\s*[,;]\s*(?:and\s+)?then\s|\s+and\s+then\s|\s*;\s*", text, maxsplit=1, flags=re.I)[0]
    text = re.sub(r"^(?:first|primero)\s*,?\s+", "", text, flags=re.I)
    text = re.sub(r"\s*,?\s+(?:first|primero)$", "", text, flags=re.I)
    return text.strip().rstrip(",.")


def sentence(text: str) -> str:
    text = text.strip()
    if text and text[-1] not in ".!?":
        text += "."
    return text


def bin_phrase(bin_cfg: dict, lang: str) -> str:
    tr = t(lang)
    return tr["bin"].format(
        color=bin_cfg["color_name"].get(lang, bin_cfg["color_name"]["en"]),
        position=tr["position"].get(bin_cfg["position"], bin_cfg["position"]),
    )
