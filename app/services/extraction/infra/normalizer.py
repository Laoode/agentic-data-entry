"""Image normalization: any input format -> canonical JPG bytes.

vLLM call site only ever receives JPG. Single source of truth keeps the
hash stable: the same logical receipt photo uploaded as PNG vs JPG
normalizes to the same JPG bytes (modulo encoder determinism — we set
fixed quality/optimize flags so JPEG output is stable).

Edge cases handled:
  - EXIF rotation (phones save sideways)
  - RGBA/LA/P modes (transparency flattened on white)
  - HEIC/HEIF (iPhone) via pillow-heif
  - Long-edge clamp keeps Qwen3.5-4B vision token budget bounded
"""

from __future__ import annotations

import io
import logging
import mimetypes
from pathlib import PurePath
from typing import Final

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Register HEIC opener with PIL. Idempotent; safe to import multiple times.
try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:  # pragma: no cover
    logger.warning("pillow-heif not installed; HEIC uploads will fail")


SUPPORTED_IMAGE_EXTENSIONS: Final = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".heic",
    ".heif",
    ".tiff",
    ".tif",
    ".bmp",
)

SUPPORTED_IMAGE_MIME_TYPES: Final = (
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
    "image/tiff",
    "image/bmp",
)

# Qwen3.5-4B vision encoder downsamples; >2048 long edge wastes tokens without
# improving recognition on receipts.
DEFAULT_MAX_LONG_EDGE = 2048
DEFAULT_JPEG_QUALITY = 92


class UnsupportedImageError(ValueError):
    pass


def is_supported_image(filename: str | None, content_type: str | None) -> bool:
    if content_type and content_type.lower() in SUPPORTED_IMAGE_MIME_TYPES:
        return True
    if filename:
        ext = PurePath(filename).suffix.lower()
        return ext in SUPPORTED_IMAGE_EXTENSIONS
    return False


def is_pdf(filename: str | None, content_type: str | None) -> bool:
    if content_type and content_type.lower() == "application/pdf":
        return True
    if filename and PurePath(filename).suffix.lower() == ".pdf":
        return True
    return False


def guess_content_type(filename: str) -> str | None:
    """Best-effort MIME from extension; covers HEIC which mimetypes misses."""
    ext = PurePath(filename).suffix.lower()
    if ext in (".heic", ".heif"):
        return "image/heif"
    return mimetypes.guess_type(filename)[0]


def to_canonical_jpg(
    data: bytes,
    *,
    max_long_edge: int = DEFAULT_MAX_LONG_EDGE,
    quality: int = DEFAULT_JPEG_QUALITY,
) -> bytes:
    """Decode any supported image and re-encode as JPG.

    Raises UnsupportedImageError if PIL can't decode it.
    """
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as e:
        raise UnsupportedImageError(f"PIL cannot decode image: {e}") from e

    img = ImageOps.exif_transpose(img)

    if img.mode in ("RGBA", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        alpha = img.split()[-1]
        background.paste(img, mask=alpha)
        img = background
    elif img.mode == "P":
        img = img.convert("RGBA")
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    if max(img.size) > max_long_edge:
        img.thumbnail((max_long_edge, max_long_edge), Image.LANCZOS)

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=quality, optimize=True)
    return out.getvalue()
