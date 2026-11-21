"""Camera frame handling: decode, resize, and prepare inspection crops.

Frames live in memory only for the length of one interaction; nothing is
written to disk unless SORTY_SAVE_FRAMES=1 is set for debugging.
"""
from __future__ import annotations

import base64
import binascii
import io

from PIL import Image, ImageFilter, ImageOps


class BadImage(ValueError):
    pass


def decode_frame(image_b64: str) -> bytes:
    """Accept raw base64 or a data: URL; return the original image bytes."""
    if not isinstance(image_b64, str) or not image_b64:
        raise BadImage("no image")
    if image_b64.startswith("data:"):
        image_b64 = image_b64.split(",", 1)[-1]
    try:
        raw = base64.b64decode(image_b64, validate=False)
    except (binascii.Error, ValueError) as exc:
        raise BadImage("image is not valid base64") from exc
    if len(raw) < 100:
        raise BadImage("image is empty")
    return raw


def _open(raw: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(raw))
        img = ImageOps.exif_transpose(img)
        return img.convert("RGB")
    except Exception as exc:  # Pillow raises many types for corrupt input
        raise BadImage("could not read the image") from exc


def _jpeg(img: Image.Image, quality: int = 88) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def _fit(img: Image.Image, max_px: int) -> Image.Image:
    if max(img.size) > max_px:
        img = img.copy()
        img.thumbnail((max_px, max_px), Image.LANCZOS)
    return img


def to_block(jpeg: bytes) -> dict:
    """A Claude image content block from JPEG bytes."""
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/jpeg",
            "data": base64.standard_b64encode(jpeg).decode("ascii"),
        },
    }


def main_view(raw: bytes, max_px: int) -> bytes:
    """The frame as the main loop sees it."""
    return _jpeg(_fit(_open(raw), max_px))


def inspection_views(raw: bytes, max_px: int) -> list[bytes]:
    """Frames for a specialist: the full view with contrast evened out, and a
    zoomed crop of the centre (where people hold the item), lightly sharpened
    so stains and small print stand out."""
    img = _open(raw)
    full = ImageOps.autocontrast(_fit(img, max_px), cutoff=1)
    w, h = img.size
    cw, ch = int(w * 0.6), int(h * 0.6)
    left, top = (w - cw) // 2, (h - ch) // 2
    crop = img.crop((left, top, left + cw, top + ch))
    scale = min(2.0, max_px / max(crop.size))
    if scale > 1.05:
        crop = crop.resize((int(crop.width * scale), int(crop.height * scale)), Image.LANCZOS)
    crop = ImageOps.autocontrast(crop, cutoff=1).filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=3))
    return [_jpeg(full, 90), _jpeg(_fit(crop, max_px), 90)]
