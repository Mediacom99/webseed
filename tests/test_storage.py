"""Layer 2: FileStorage tests — LocalFileStorage with tmp_path."""

from __future__ import annotations

import os
from pathlib import Path

from webseed.storage import LocalFileStorage


class TestSiteDir:
    def test_creates_directory(self, file_storage: LocalFileStorage) -> None:
        path = file_storage.site_dir("test-biz")
        assert os.path.isdir(path)
        assert os.path.isabs(path)


class TestPhotoDir:
    def test_creates_nested_img_dir(self, file_storage: LocalFileStorage) -> None:
        path = file_storage.photo_dir("test-biz")
        assert os.path.isdir(path)
        assert path.endswith(os.path.join("test-biz", "img"))


class TestScreenshotsDir:
    def test_creates_screenshots_dir(self, file_storage: LocalFileStorage) -> None:
        path = file_storage.screenshots_dir()
        assert os.path.isdir(path)
        assert path.endswith("screenshots")


class TestWriteFile:
    def test_string_content(self, file_storage: LocalFileStorage) -> None:
        abs_path = file_storage.write_file("test-biz/index.html", "<html>test</html>")
        assert os.path.isfile(abs_path)
        assert os.path.isabs(abs_path)
        with open(abs_path) as f:
            assert f.read() == "<html>test</html>"

    def test_bytes_content(self, file_storage: LocalFileStorage) -> None:
        data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        abs_path = file_storage.write_file("test-biz/img/photo.jpg", data)
        assert os.path.isfile(abs_path)
        with open(abs_path, "rb") as f:
            assert f.read() == data


class TestReadFile:
    def test_roundtrip(self, file_storage: LocalFileStorage) -> None:
        file_storage.write_file("roundtrip.txt", "hello world")
        content = file_storage.read_file("roundtrip.txt")
        assert content == "hello world"


class TestExists:
    def test_existing_file(self, file_storage: LocalFileStorage) -> None:
        file_storage.write_file("exists.txt", "yes")
        assert file_storage.exists("exists.txt") is True

    def test_nonexistent_file(self, file_storage: LocalFileStorage) -> None:
        assert file_storage.exists("nope.txt") is False


class TestListFiles:
    def test_glob_pattern(self, file_storage: LocalFileStorage) -> None:
        file_storage.write_file("listing/a.txt", "a")
        file_storage.write_file("listing/b.txt", "b")
        file_storage.write_file("listing/c.log", "c")
        txt_files = file_storage.list_files("listing", "*.txt")
        assert len(txt_files) == 2


class TestDeleteDir:
    def test_removes_directory(self, file_storage: LocalFileStorage) -> None:
        file_storage.write_file("delme/file.txt", "x")
        assert file_storage.exists("delme/file.txt")
        file_storage.delete_dir("delme")
        assert not file_storage.exists("delme/file.txt")
        # The directory itself should be gone
        assert not file_storage.exists("delme")
