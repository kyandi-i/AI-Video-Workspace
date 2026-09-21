"""Local media decoding; no network protocols, extensions are only an allowlist."""

import math
import warnings
from dataclasses import dataclass
from pathlib import Path

import av
from PIL import Image, ImageOps

from app.core.exceptions import AppError

EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".webm"}
MAX_PIXELS = 40_000_000


@dataclass
class MediaInfo:
    mime_type: str
    width: int
    height: int
    duration_seconds: float | None


def decode_preview(path: Path):
    """Validate image payload or video container and first decodable video frame."""
    try:
        with path.open("rb") as source:
            signature = source.read(32)
        image_format = (
            "PNG"
            if signature.startswith(b"\x89PNG\r\n\x1a\n")
            else "JPEG"
            if signature.startswith(b"\xff\xd8\xff")
            else "WEBP"
            if signature.startswith(b"RIFF") and signature[8:12] == b"WEBP"
            else None
        )
        if image_format:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(path, formats=[image_format]) as probe:
                    if probe.width * probe.height > MAX_PIXELS:
                        raise ValueError("Image too large")
                    probe.verify()
                with Image.open(path, formats=[image_format]) as original:
                    preview = ImageOps.exif_transpose(original)
                    width, height = preview.size
                    preview.thumbnail((512, 512))
                    preview = preview.convert("RGB")
            return MediaInfo(Image.MIME[image_format], width, height, None), preview
        is_mp4 = signature[4:8] == b"ftyp"
        is_webm = signature.startswith(b"\x1aE\xdf\xa3")
        if not is_mp4 and not is_webm:
            raise ValueError("Unsupported signature")
        # File-like input plus a protocol allowlist prevents indirect URL/playlist reads.
        with (
            path.open("rb") as source,
            av.open(source, options={"protocol_whitelist": "file"}) as container,
        ):
            if not container.streams.video:
                raise ValueError("No video stream")
            stream = container.streams.video[0]
            if stream.width * stream.height > MAX_PIXELS:
                raise ValueError("Video too large")
            stream.thread_count = 1
            frame = next(container.decode(stream))
            duration = (
                float(stream.duration * stream.time_base)
                if stream.duration is not None
                else float(container.duration / av.time_base)
                if container.duration
                else None
            )
            if duration is None or not math.isfinite(duration) or duration <= 0:
                raise ValueError("No valid video duration")
            mime = (
                "video/webm"
                if is_webm
                else ("video/quicktime" if signature[8:12] == b"qt  " else "video/mp4")
            )
            preview = frame.to_image()
            preview.thumbnail((512, 512))
            return MediaInfo(mime, frame.width, frame.height, duration), preview.convert("RGB")
    except (
        ValueError,
        OSError,
        StopIteration,
        av.FFmpegError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise AppError(
            "INVALID_MEDIA", "文件损坏、格式不支持或媒体尺寸超过限制，请选择有效图片或视频。", 422
        ) from exc
