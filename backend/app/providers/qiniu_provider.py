"""
Qiniu Kodo provider.

Only handles external Qiniu SDK calls.
Business code should call app.services.storage_service instead.
"""
import os
import tempfile
from typing import Optional

from qiniu import Auth, put_file_v2
from qiniu.http.region import Region

from app.core.config import settings
from app.utils.logger import app_logger


class QiniuProvider:
    """Qiniu Kodo upload provider."""

    def __init__(self):
        self.access_key = settings.QINIU_ACCESS_KEY
        self.secret_key = settings.QINIU_SECRET_KEY
        self.bucket = settings.QINIU_BUCKET
        self.domain = settings.QINIU_DOMAIN.rstrip("/") if settings.QINIU_DOMAIN else ""
        self.region_id = settings.QINIU_REGION_ID
        self.private_bucket = settings.QINIU_PRIVATE_BUCKET
        self.private_url_expires = settings.QINIU_PRIVATE_URL_EXPIRES

    def _validate_config(self):
        if not self.access_key:
            raise ValueError("QINIU_ACCESS_KEY is not configured")
        if not self.secret_key:
            raise ValueError("QINIU_SECRET_KEY is not configured")
        if not self.bucket:
            raise ValueError("QINIU_BUCKET is not configured")
        if not self.domain:
            raise ValueError("QINIU_DOMAIN is not configured")

    def _auth(self) -> Auth:
        self._validate_config()
        return Auth(self.access_key, self.secret_key)

    def _regions(self):
        if not self.region_id:
            return None

        return [Region.from_region_id(self.region_id)]

    def build_public_url(self, key: str) -> str:
        self._validate_config()
        return f"{self.domain}/{key.lstrip('/')}"

    def build_private_url(self, key: str, expires: Optional[int] = None) -> str:
        """
        Build a temporary private download URL for Qiniu private bucket.
        """
        q = self._auth()
        base_url = self.build_public_url(key)
        return q.private_download_url(
            base_url,
            expires=expires or self.private_url_expires,
        )

    def build_access_url(self, key: str) -> str:
        """
        Build frontend-accessible URL.

        Public bucket: return normal public URL.
        Private bucket: return temporary signed URL.
        """
        if self.private_bucket:
            return self.build_private_url(key)

        return self.build_public_url(key)

    def upload_file(self, local_path: str, key: str) -> dict:
        """
        Upload a local file to Qiniu.

        Returns:
            {
                "key": "...",
                "hash": "...",
                "url": "https://..."
            }
        """
        q = self._auth()
        token = q.upload_token(self.bucket, key, 3600)

        proxy_keys = (
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ALL_PROXY",
            "http_proxy",
            "https_proxy",
            "all_proxy",
        )
        old_proxy_env = {name: os.environ.get(name) for name in proxy_keys}

        try:
            for name in proxy_keys:
                os.environ.pop(name, None)

            ret, info = put_file_v2(
                token,
                key,
                local_path,
                version="v2",
                bucket_name=self.bucket,
                regions=self._regions(),
            )
        finally:
            for name, value in old_proxy_env.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value

        if info.status_code != 200:
            app_logger.error(
                f"Qiniu upload failed: key={key}, status={info.status_code}, error={info.error}"
            )
            raise RuntimeError(f"七牛云上传失败: {info.error or info.status_code}")

        if not ret or ret.get("key") != key:
            app_logger.error(f"Qiniu upload response invalid: key={key}, ret={ret}")
            raise RuntimeError("七牛云上传返回异常")

        url = self.build_public_url(key)
        app_logger.info(f"Qiniu upload success: key={key}, url={url}")

        return {
            "key": ret.get("key"),
            "hash": ret.get("hash"),
            "url": url,
        }

    def upload_bytes(self, data: bytes, key: str, suffix: Optional[str] = None) -> dict:
        """
        Upload bytes by writing a temporary file first.

        This follows the official put_file_v2 upload path and avoids relying on
        SDK methods not used in the official example.
        """
        fd = None
        temp_path = None

        try:
            fd, temp_path = tempfile.mkstemp(suffix=suffix or "")
            with os.fdopen(fd, "wb") as f:
                fd = None
                f.write(data)

            return self.upload_file(temp_path, key)

        finally:
            if fd is not None:
                os.close(fd)
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)


qiniu_provider = QiniuProvider()