"""Shared utility helpers."""

import os
import tempfile


def atomic_write(path: str, content: str) -> None:
    """Write *content* to *path* atomically via temp-file + rename.

    If interrupted mid-write the original file is left untouched.
    """
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
