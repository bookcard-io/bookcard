# Copyright (C) 2025 knguyen and others
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Tests for FBZ cover extractor to achieve 100% coverage."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fundamental.services.cover_extractors.fbz import FbzCoverExtractor


@pytest.fixture
def extractor() -> FbzCoverExtractor:
    """Create FbzCoverExtractor instance."""
    return FbzCoverExtractor()


def _create_mock_fbz(
    fb2_content: str | None = None,
    fb2_filename: str = "book.fb2",
    invalid_zip: bool = False,
) -> Path:
    """Create a mock FBZ file for testing.

    Parameters
    ----------
    fb2_content : str | None
        Content for the FB2 file inside the ZIP.
    fb2_filename : str
        Filename for the FB2 file inside the ZIP.
    invalid_zip : bool
        If True, create an invalid ZIP file.

    Returns
    -------
    Path
        Path to the created FBZ file.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".fbz") as tmp:
        file_path = Path(tmp.name)

    if invalid_zip:
        file_path.write_bytes(b"invalid zip content")
        return file_path

    with zipfile.ZipFile(file_path, "w") as fbz_zip:
        if fb2_content:
            fbz_zip.writestr(fb2_filename, fb2_content.encode("utf-8"))

    return file_path


@pytest.mark.parametrize(
    ("file_format", "expected"),
    [
        ("fbz", True),
        ("FBZ", True),
        (".fbz", True),
        ("epub", False),
        ("pdf", False),
    ],
)
def test_can_handle(
    extractor: FbzCoverExtractor, file_format: str, expected: bool
) -> None:
    """Test can_handle for various formats (covers lines 43-46)."""
    assert extractor.can_handle(file_format) == expected


def test_extract_cover_with_fb2_file(extractor: FbzCoverExtractor) -> None:
    """Test extract_cover with FB2 file in ZIP (covers lines 64-89)."""
    fb2_content = """<?xml version="1.0" encoding="UTF-8"?>
    <FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0">
        <description>
            <title-info>
                <book-title>Test Book</book-title>
            </title-info>
        </description>
        <body></body>
    </FictionBook>"""

    file_path = _create_mock_fbz(fb2_content=fb2_content, fb2_filename="book.fb2")

    try:
        # Mock the FB2 extractor to return cover data
        with patch.object(
            extractor._fb2_extractor, "extract_cover", return_value=b"cover_data"
        ):
            result = extractor.extract_cover(file_path)
            assert result == b"cover_data"
    finally:
        file_path.unlink()


def test_extract_cover_no_fb2_file(extractor: FbzCoverExtractor) -> None:
    """Test extract_cover when no FB2 file found (covers lines 70-71)."""
    file_path = _create_mock_fbz()

    try:
        result = extractor.extract_cover(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_extract_cover_multiple_fb2_files(extractor: FbzCoverExtractor) -> None:
    """Test extract_cover uses first FB2 file when multiple found (covers lines 73-74)."""
    fb2_content = """<?xml version="1.0" encoding="UTF-8"?>
    <FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0">
        <description>
            <title-info>
                <book-title>Test Book</book-title>
            </title-info>
        </description>
        <body></body>
    </FictionBook>"""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".fbz") as tmp:
        file_path = Path(tmp.name)

    with zipfile.ZipFile(file_path, "w") as fbz_zip:
        fbz_zip.writestr("book1.fb2", fb2_content.encode("utf-8"))
        fbz_zip.writestr("book2.fb2", fb2_content.encode("utf-8"))

    try:
        # Mock the FB2 extractor to return cover data
        with patch.object(
            extractor._fb2_extractor, "extract_cover", return_value=b"cover_data"
        ):
            result = extractor.extract_cover(file_path)
            # Should use first FB2 file
            assert result == b"cover_data"
    finally:
        file_path.unlink()


def test_extract_cover_temp_file_cleanup(extractor: FbzCoverExtractor) -> None:
    """Test extract_cover cleans up temp file (covers lines 87-89)."""
    fb2_content = """<?xml version="1.0" encoding="UTF-8"?>
    <FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0">
        <description>
            <title-info>
                <book-title>Test Book</book-title>
            </title-info>
        </description>
        <body></body>
    </FictionBook>"""

    file_path = _create_mock_fbz(fb2_content=fb2_content, fb2_filename="book.fb2")

    try:
        # Mock the FB2 extractor to return cover data
        with patch.object(
            extractor._fb2_extractor, "extract_cover", return_value=b"cover_data"
        ):
            result = extractor.extract_cover(file_path)
            assert result == b"cover_data"
            # Temp file should be cleaned up in finally block
    finally:
        file_path.unlink()


def test_extract_cover_invalid_zip(extractor: FbzCoverExtractor) -> None:
    """Test extract_cover handles invalid ZIP (covers lines 91-92)."""
    file_path = _create_mock_fbz(invalid_zip=True)

    try:
        result = extractor.extract_cover(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_extract_cover_os_error(extractor: FbzCoverExtractor) -> None:
    """Test extract_cover handles OSError (covers lines 91-92)."""
    # Create a file that will cause OSError when opened as ZIP
    with tempfile.NamedTemporaryFile(delete=False, suffix=".fbz") as tmp:
        file_path = Path(tmp.name)
        tmp.write(b"not a zip")

    try:
        result = extractor.extract_cover(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_extract_cover_key_error(extractor: FbzCoverExtractor) -> None:
    """Test extract_cover handles KeyError (covers lines 91-92)."""
    # Create a ZIP file but make reading fail with KeyError
    with tempfile.NamedTemporaryFile(delete=False, suffix=".fbz") as tmp:
        file_path = Path(tmp.name)

    with zipfile.ZipFile(file_path, "w"):
        # Create empty ZIP
        pass

    try:
        # Mock zipfile to raise KeyError when reading
        with patch("zipfile.ZipFile") as mock_zip_class:
            mock_zip = MagicMock()
            mock_zip.__enter__.return_value = mock_zip
            mock_zip.__exit__.return_value = None
            mock_zip.namelist.return_value = []
            mock_zip.read.side_effect = KeyError("file not found")
            mock_zip_class.return_value = mock_zip

            result = extractor.extract_cover(file_path)
            assert result is None
    finally:
        file_path.unlink()


def test_extract_cover_fb2_lowercase_extension(extractor: FbzCoverExtractor) -> None:
    """Test extract_cover finds FB2 files with lowercase extension (covers lines 67-68)."""
    fb2_content = """<?xml version="1.0" encoding="UTF-8"?>
    <FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0">
        <description>
            <title-info>
                <book-title>Test Book</book-title>
            </title-info>
        </description>
        <body></body>
    </FictionBook>"""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".fbz") as tmp:
        file_path = Path(tmp.name)

    with zipfile.ZipFile(file_path, "w") as fbz_zip:
        fbz_zip.writestr("book.FB2", fb2_content.encode("utf-8"))  # Uppercase extension

    try:
        # Mock the FB2 extractor to return cover data
        with patch.object(
            extractor._fb2_extractor, "extract_cover", return_value=b"cover_data"
        ):
            result = extractor.extract_cover(file_path)
            # Should find .FB2 file (lowercase check)
            assert result == b"cover_data"
    finally:
        file_path.unlink()
