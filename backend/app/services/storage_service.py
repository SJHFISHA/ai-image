"""
Storage service.

This layer converts generated media values into bytes and uploads them to
configured object storage. It should be used by generation_service.
"""
import base64
import mimetypes
from datetime import datetime
from app.utils.timezone import now_beijing_naive
from typing import Iterable, Optional
from urllib.parse import urlparse

import requests

from app.providers.qiniu_provider import qiniu_provider
from app.utils.logger import app_logger


_IMAGE_EXT_BY_MIME = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
}

_VIDEO_EXT_BY_MIME = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
}


def _split_data_url(value: str) -> tuple[Optional[str], str]:
    if not value.startswith("data:"):
        return None, value

    header, encoded = value.split(",", 1)
    mime_type = header.removeprefix("data:").split(";")[0]
    return mime_type, encoded


def _guess_suffix(mime_type: Optional[str], media_type: str, source_url: Optional[str] = None) -> str:
    if mime_type:
        if media_type == "image" and mime_type in _IMAGE_EXT_BY_MIME:
            return _IMAGE_EXT_BY_MIME[mime_type]
        if media_type == "video" and mime_type in _VIDEO_EXT_BY_MIME:
            return _VIDEO_EXT_BY_MIME[mime_type]

        guessed = mimetypes.guess_extension(mime_type)
        if guessed:
            return guessed

    if source_url:
        path = urlparse(source_url).path
        guessed = mimetypes.guess_type(path)[0]
        if guessed:
            ext = mimetypes.guess_extension(guessed)
            if ext:
                return ext

    return ".mp4" if media_type == "video" else ".png"


def _download_url(url: str) -> tuple[bytes, Optional[str]]:
    session = requests.Session()
    session.trust_env = False

    response = session.get(url, timeout=120)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type")
    if content_type:
        content_type = content_type.split(";")[0].strip().lower()

    return response.content, content_type


def _decode_media_value(value: str, media_type: str) -> tuple[bytes, Optional[str], str]:
    """
    Decode a generated media value.

    Supports:
    - public http/https URL
    - data URL, such as data:image/png;base64,...
    - raw base64 string
    """
    if value.startswith("http://") or value.startswith("https://"):
        data, mime_type = _download_url(value)
        suffix = _guess_suffix(mime_type, media_type, source_url=value)
        return data, mime_type, suffix

    mime_type, encoded = _split_data_url(value)

    try:
        data = base64.b64decode(encoded)
    except Exception as exc:
        raise ValueError("生成结果不是有效的 URL 或 base64 数据") from exc

    suffix = _guess_suffix(mime_type, media_type)
    return data, mime_type, suffix


def build_object_key(
    *,
    user_id: int,
    task_id: str,
    media_type: str,
    index: int,
    suffix: str,
) -> str:
    now = now_beijing_naive()
    clean_suffix = suffix if suffix.startswith(".") else f".{suffix}"

    return (
        f"ai-generated/{media_type}/"
        f"{now:%Y/%m/%d}/"
        f"user_{user_id}/"
        f"{task_id}_{index}{clean_suffix}"
    )


def upload_generated_media(
    *,
    value: str,
    user_id: int,
    task_id: str,
    media_type: str,
    index: int,
) -> dict:
    """
    Upload one generated image/video result to Qiniu.

    Returns:
        {
            "url": "...",
            "key": "...",
            "hash": "...",
            "mime_type": "image/png",
            "media_type": "image"
        }
    """
    data, mime_type, suffix = _decode_media_value(value, media_type)

    key = build_object_key(
        user_id=user_id,
        task_id=task_id,
        media_type=media_type,
        index=index,
        suffix=suffix,
    )

    upload_result = qiniu_provider.upload_bytes(data, key, suffix=suffix)

    return {
        "url": upload_result["url"],
        "key": upload_result["key"],
        "hash": upload_result.get("hash"),
        "mime_type": mime_type,
        "media_type": media_type,
    }


def upload_generated_media_list(
    *,
    values: Iterable[str],
    user_id: int,
    task_id: str,
    media_type: str,
) -> list[dict]:
    uploaded = []

    for index, value in enumerate(values, start=1):
        uploaded.append(
            upload_generated_media(
                value=value,
                user_id=user_id,
                task_id=task_id,
                media_type=media_type,
                index=index,
            )
        )

    app_logger.info(
        f"Generated media uploaded: task_id={task_id}, media_type={media_type}, count={len(uploaded)}"
    )

    return uploaded