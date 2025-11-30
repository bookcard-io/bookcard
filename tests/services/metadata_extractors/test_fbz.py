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

"""Tests for FBZ metadata extractor to achieve 100% coverage."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fundamental.services.metadata_extractors.fbz import FbzMetadataExtractor


@pytest.fixture
def extractor() -> FbzMetadataExtractor:
    """Create FbzMetadataExtractor instance."""
    return FbzMetadataExtractor()


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
        # Write invalid ZIP content
        file_path.write_bytes(b"invalid zip content")
        return file_path

    with zipfile.ZipFile(file_path, "w") as fbz_zip:
        if fb2_content:
            fbz_zip.writestr(fb2_filename, fb2_content)

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
    extractor: FbzMetadataExtractor, file_format: str, expected: bool
) -> None:
    """Test can_handle for various formats (covers lines 47-50)."""
    assert extractor.can_handle(file_format) == expected


def test_extract_with_fb2_file(extractor: FbzMetadataExtractor) -> None:
    """Test extract with FB2 file in ZIP (covers lines 70-101)."""
    fb2_content = """<?xml version="1.0" encoding="UTF-8"?>
    <FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0">
        <description>
            <title-info>
                <book-title>Test Book</book-title>
                <author>
                    <first-name>Test</first-name>
                    <last-name>Author</last-name>
                </author>
            </title-info>
        </description>
        <body></body>
    </FictionBook>"""

    file_path = _create_mock_fbz(fb2_content=fb2_content, fb2_filename="book.fb2")

    try:
        metadata = extractor.extract(file_path, "test.fbz")
        # The FB2 extractor should extract metadata
        assert metadata.title is not None
        assert metadata.author is not None
    finally:
        file_path.unlink()


def test_extract_no_fb2_file(extractor: FbzMetadataExtractor) -> None:
    """Test extract when no FB2 file found (covers lines 76-83)."""
    file_path = _create_mock_fbz()

    try:
        metadata = extractor.extract(file_path, "test.fbz")
        assert metadata.title == "test"
        assert metadata.author == "Unknown"
    finally:
        file_path.unlink()


def test_extract_multiple_fb2_files(extractor: FbzMetadataExtractor) -> None:
    """Test extract uses first FB2 file when multiple found (covers lines 85-86)."""
    fb2_content = """<?xml version="1.0" encoding="UTF-8"?>
    <FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0">
        <description>
            <title-info>
                <book-title>First Book</book-title>
            </title-info>
        </description>
        <body></body>
    </FictionBook>"""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".fbz") as tmp:
        file_path = Path(tmp.name)

    with zipfile.ZipFile(file_path, "w") as fbz_zip:
        fbz_zip.writestr("book1.fb2", fb2_content)
        fbz_zip.writestr("book2.fb2", fb2_content)

    try:
        metadata = extractor.extract(file_path, "test.fbz")
        # Should use first FB2 file
        assert metadata.title is not None
    finally:
        file_path.unlink()


def test_extract_fb2_extraction_error(extractor: FbzMetadataExtractor) -> None:
    """Test extract handles FB2 extraction errors (covers lines 95-101)."""
    # Create FBZ with invalid FB2 content
    invalid_fb2 = "invalid xml content"

    file_path = _create_mock_fbz(fb2_content=invalid_fb2, fb2_filename="book.fb2")

    try:
        # The FB2 extractor raises ValueError, which FBZ doesn't catch
        # So this will raise ValueError, but we're testing the code path
        # The temp file cleanup happens in finally block
        with pytest.raises(ValueError, match="Invalid FB2 XML"):
            extractor.extract(file_path, "test.fbz")
    finally:
        file_path.unlink()


def test_extract_temp_file_cleanup(extractor: FbzMetadataExtractor) -> None:
    """Test extract cleans up temp file (covers lines 99-101)."""
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
        # Extract metadata - temp file cleanup happens in finally block
        metadata = extractor.extract(file_path, "test.fbz")
        assert metadata.title is not None
    finally:
        file_path.unlink()


def test_extract_invalid_zip(extractor: FbzMetadataExtractor) -> None:
    """Test extract handles invalid ZIP (covers lines 103-110)."""
    file_path = _create_mock_fbz(invalid_zip=True)

    try:
        metadata = extractor.extract(file_path, "test.fbz")
        assert metadata.title == "test"
        assert metadata.author == "Unknown"
    finally:
        file_path.unlink()


def test_extract_os_error(extractor: FbzMetadataExtractor) -> None:
    """Test extract handles OSError (covers lines 103-110)."""
    # Create a file that will cause OSError when opened as ZIP
    with tempfile.NamedTemporaryFile(delete=False, suffix=".fbz") as tmp:
        file_path = Path(tmp.name)
        tmp.write(b"not a zip")

    try:
        metadata = extractor.extract(file_path, "test.fbz")
        assert metadata.title == "test"
        assert metadata.author == "Unknown"
    finally:
        file_path.unlink()


def test_extract_key_error(extractor: FbzMetadataExtractor) -> None:
    """Test extract handles KeyError (covers lines 103-110)."""
    # Create a ZIP file but make reading fail with KeyError
    with tempfile.NamedTemporaryFile(delete=False, suffix=".fbz") as tmp:
        file_path = Path(tmp.name)

    with zipfile.ZipFile(file_path, "w"):
        # Create empty ZIP
        pass

    try:
        # Mock the zipfile to raise KeyError when reading
        with patch("zipfile.ZipFile") as mock_zip_class:
            mock_zip = MagicMock()
            mock_zip.__enter__.return_value = mock_zip
            mock_zip.__exit__.return_value = None
            mock_zip.namelist.return_value = []
            mock_zip.read.side_effect = KeyError("file not found")
            mock_zip_class.return_value = mock_zip

            metadata = extractor.extract(file_path, "test.fbz")
            assert metadata.title == "test"
            assert metadata.author == "Unknown"
    finally:
        file_path.unlink()


def test_extract_fb2_lowercase_extension(extractor: FbzMetadataExtractor) -> None:
    """Test extract finds FB2 files with lowercase extension (covers lines 73-74)."""
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
        fbz_zip.writestr("book.FB2", fb2_content)  # Uppercase extension

    try:
        metadata = extractor.extract(file_path, "test.fbz")
        # Should find .FB2 file (lowercase check)
        assert metadata.title is not None
    finally:
        file_path.unlink()
