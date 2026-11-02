# app/images.py
from __future__ import annotations

import hashlib
import io
from datetime import datetime, timezone

from PIL import Image, ImageOps

from app.storage import get_storage


ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_DIMENSION = 2400        # max width/height for the full image
THUMB_DIMENSION = 400       # max dimension for the thumbnail
WEBP_QUALITY = 85


def _safe_extension(mime: str) -> str:
    return {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
    }.get(mime, "jpg")


def _storage_key(prefix: str, ext: str) -> str:
    now = datetime.now(timezone.utc)
    h = hashlib.sha1(f"{now.timestamp()}-{ext}".encode()).hexdigest()[:16]
    return f"{prefix}/{now.year}/{now.month:02d}/{h}.{ext}"


def _storage_thumb_key(key: str) -> str:
    # e.g. "gallery/2026/10/abc123.jpg" -> "gallery/2026/10/abc123_thumb.jpg"
    if "." not in key:
        return key + "_thumb"
    stem, ext = key.rsplit(".", 1)
    return f"{stem}_thumb.{ext}"


def process_and_store_image(
    *,
    file_bytes: bytes,
    mime_type: str,
    prefix: str = "gallery",
) -> dict:
    """
    Takes raw uploaded bytes, validates, resizes, converts to WebP,
    stores both full and thumbnail, returns metadata.

    Returns:
      {
        "key": "...", "url": "...",
        "thumb_key": "...", "thumb_url": "...",
        "width": int, "height": int,
        "size_bytes": int, "mime_type": "image/webp",
      }
    """
    if mime_type not in ALLOWED_MIME:
        raise ValueError(f"Unsupported image type: {mime_type}")

    try:
        img = Image.open(io.BytesIO(file_bytes))
        img = ImageOps.exif_transpose(img)  # respect orientation
    except Exception as e:
        raise ValueError(f"Could not read image: {e}")

    # Convert to RGB (WebP doesn't support CMYK)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Resize if too large
    img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

    # Encode to WebP
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=WEBP_QUALITY, method=6)
    webp_bytes = buf.getvalue()

    # Thumbnail
    thumb = img.copy()
    thumb.thumbnail((THUMB_DIMENSION, THUMB_DIMENSION), Image.LANCZOS)
    tbuf = io.BytesIO()
    thumb.save(tbuf, format="WEBP", quality=WEBP_QUALITY, method=6)
    thumb_bytes = tbuf.getvalue()

    # Store
    storage = get_storage()
    key = _storage_key(prefix, "webp")
    thumb_key = _storage_thumb_key(key)

    storage.write(key, webp_bytes)
    storage.write(thumb_key, thumb_bytes)

    # Build relative public URLs.
# These work through the frontend proxy, LAN IP and HTTPS tunnels.
    url = f"/api/v1/gallery/files/{key}"
    thumb_url = f"/api/v1/gallery/files/{thumb_key}"

    return {
        "key": key,
        "url": url,
        "thumb_key": thumb_key,
        "thumb_url": thumb_url,
        "width": img.width,
        "height": img.height,
        "size_bytes": len(webp_bytes),
        "mime_type": "image/webp",
    }


def delete_image(key: str) -> None:
    """Delete both full and thumbnail."""
    storage = get_storage()
    try:
        storage.delete(key)
    except Exception:
        pass
    try:
        storage.delete(_storage_thumb_key(key))
    except Exception:
        pass