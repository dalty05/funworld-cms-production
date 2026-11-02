# app/storage.py
from __future__ import annotations

import os
import shutil
from pathlib import Path

from flask import current_app


class StorageBackend:
    def write(self, key: str, data: bytes) -> str:
        """Write bytes under `key`. Returns a canonical storage URL/path."""
        raise NotImplementedError

    def read(self, key: str) -> bytes:
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError

    def url_for(self, key: str) -> str:
        """Return something the caller can hand to a browser (optional)."""
        return key


class LocalStorage(StorageBackend):
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Prevent path traversal
        safe = Path(key)
        if safe.is_absolute() or ".." in safe.parts:
            raise ValueError(f"Unsafe storage key: {key}")
        return self.root / safe

    def write(self, key: str, data: bytes) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)  # atomic on the same filesystem
        return str(path)

    def read(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def delete(self, key: str) -> None:
        p = self._path(key)
        if p.exists():
            p.unlink()

    def url_for(self, key: str) -> str:
        return str(self._path(key))


class S3Storage(StorageBackend):
    """Stub for future S3 swap. Implement when needed."""

    def __init__(self, bucket: str):
        self.bucket = bucket
        # from boto3 import client; self.client = client("s3"); ...

    def write(self, key: str, data: bytes) -> str:
        raise NotImplementedError("S3 backend not implemented yet")

    def read(self, key: str) -> bytes:
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError


def get_storage() -> StorageBackend:
    backend = current_app.config.get("DOCUMENT_STORAGE_BACKEND", "local")
    if backend == "s3":
        return S3Storage(current_app.config["S3_BUCKET"])
    return LocalStorage(current_app.config.get("DOCUMENT_LOCAL_ROOT",
                                                "./storage/documents"))