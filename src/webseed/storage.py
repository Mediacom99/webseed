"""File storage implementation — local filesystem adapter."""

from __future__ import annotations

import glob as glob_module
import os
import shutil
import tempfile


def _atomic_write(path: str, content: str) -> None:
    """Write *content* to *path* atomically via temp-file + rename."""
    dir_name = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


class LocalFileStorage:
    """FileStoragePort implementation backed by local filesystem."""

    def __init__(self, base_dir: str) -> None:
        self._base = os.path.abspath(base_dir)

    def _abs(self, relative_path: str) -> str:
        return os.path.join(self._base, relative_path)

    def site_dir(self, name_slug: str) -> str:
        path = self._abs(name_slug)
        os.makedirs(path, exist_ok=True)
        return path

    def photo_dir(self, name_slug: str) -> str:
        path = self._abs(os.path.join(name_slug, "img"))
        os.makedirs(path, exist_ok=True)
        return path

    def screenshots_dir(self) -> str:
        path = self._abs("screenshots")
        os.makedirs(path, exist_ok=True)
        return path

    def write_file(self, relative_path: str, content: str | bytes) -> str:
        abs_path = self._abs(relative_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        if isinstance(content, str):
            _atomic_write(abs_path, content)
        else:
            with open(abs_path, "wb") as f:
                f.write(content)
        return abs_path

    def read_file(self, relative_path: str) -> str:
        abs_path = self._abs(relative_path)
        with open(abs_path, "r", encoding="utf-8") as f:
            return f.read()

    def exists(self, relative_path: str) -> bool:
        return os.path.exists(self._abs(relative_path))

    def list_files(self, relative_path: str, pattern: str = "*") -> list[str]:
        search_path = os.path.join(self._abs(relative_path), pattern)
        return sorted(glob_module.glob(search_path))

    def delete_dir(self, relative_path: str) -> None:
        abs_path = self._abs(relative_path)
        if os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
