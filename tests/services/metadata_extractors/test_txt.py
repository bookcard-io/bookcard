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

"""Tests for TXT metadata extractor to achieve 100% coverage."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from bookcard.services.metadata_extractors.txt import TxtMetadataExtractor


@pytest.fixture
def extractor() -> TxtMetadataExtractor:
    """Create TxtMetadataExtractor instance."""
    return TxtMetadataExtractor()


def _create_mock_txt_file(txt_content: str) -> Path:
    """Create a mock TXT file for testing.

    Parameters
    ----------
    txt_content : str
        Text content to write.

    Returns
    -------
    Path
        Path to the created TXT file.
    """
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".txt", mode="w", encoding="utf-8"
    ) as tmp:
        file_path = Path(tmp.name)
        tmp.write(txt_content)

    return file_path


@pytest.mark.parametrize(
    ("file_format", "expected"),
    [
        ("txt", True),
        ("TXT", True),
        ("txtz", True),
        ("TXTZ", True),
        (".txt", True),
        ("epub", False),
        ("pdf", False),
    ],
)
def test_can_handle(
    extractor: TxtMetadataExtractor, file_format: str, expected: bool
) -> None:
    """Test can_handle for various formats (covers lines 52-55)."""
    assert extractor.can_handle(file_format) == expected


def test_extract_txtz(extractor: TxtMetadataExtractor) -> None:
    """Test extract with TXTZ file (covers lines 74-77)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txtz") as tmp:
        file_path = Path(tmp.name)

    try:
        metadata = extractor.extract(file_path, "test.txtz")
        assert metadata.title == "test"
        assert metadata.author == "Unknown"
    finally:
        file_path.unlink()


def test_extract_with_title_pattern(extractor: TxtMetadataExtractor) -> None:
    """Test extract with title pattern (covers lines 79-90)."""
    txt_content = """Title: Test Book
Author: Test Author
Content here...
"""

    file_path = _create_mock_txt_file(txt_content)

    try:
        metadata = extractor.extract(file_path, "test.txt")
        assert metadata.title == "Test Book"
        assert metadata.author == "Test Author"
    finally:
        file_path.unlink()


def test_extract_os_error(extractor: TxtMetadataExtractor) -> None:
    """Test extract handles OSError (covers lines 91-93)."""
    # Create a non-existent file path
    file_path = Path("/nonexistent/path/test.txt")

    metadata = extractor.extract(file_path, "test.txt")
    assert metadata.title == "test"
    assert metadata.author == "Unknown"


def test_extract_unicode_decode_error(extractor: TxtMetadataExtractor) -> None:
    """Test extract handles UnicodeDecodeError (covers lines 91-93)."""
    # Create a file with invalid UTF-8
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="wb") as tmp:
        file_path = Path(tmp.name)
        # Write invalid UTF-8 bytes
        tmp.write(b"\xff\xfe\x00\x00")

    try:
        metadata = extractor.extract(file_path, "test.txt")
        assert metadata.title == "test"
        assert metadata.author == "Unknown"
    finally:
        file_path.unlink()


def test_extract_title_title_colon(extractor: TxtMetadataExtractor) -> None:
    """Test _extract_title with title: pattern (covers lines 111-119)."""
    content = "Title: Test Book\nContent here"
    title = extractor._extract_title(content, "test.txt")
    assert title == "Test Book"


def test_extract_title_markdown(extractor: TxtMetadataExtractor) -> None:
    """Test _extract_title with markdown pattern (covers lines 111-119)."""
    content = "# Test Book\nContent here"
    title = extractor._extract_title(content, "test.txt")
    assert title == "Test Book"


def test_extract_title_underlined_equals(extractor: TxtMetadataExtractor) -> None:
    """Test _extract_title with underlined title (equals) (covers lines 111-119)."""
    content = "Test Book\n===="
    title = extractor._extract_title(content, "test.txt")
    assert title == "Test Book"


def test_extract_title_underlined_dashes(extractor: TxtMetadataExtractor) -> None:
    """Test _extract_title with underlined title (dashes) (covers lines 111-119)."""
    content = "Test Book\n----"
    title = extractor._extract_title(content, "test.txt")
    assert title == "Test Book"


def test_extract_title_too_long(extractor: TxtMetadataExtractor) -> None:
    """Test _extract_title with title too long (covers lines 115-116)."""
    # Create a title longer than 200 characters
    long_title = "A" * 250
    content = f"Title: {long_title}\nContent"
    title = extractor._extract_title(content, "test.txt")
    # Should fall back to filename
    assert title == "test"


def test_extract_title_fallback(extractor: TxtMetadataExtractor) -> None:
    """Test _extract_title falls back to filename (covers lines 118-119)."""
    content = "No title pattern here\nContent"
    title = extractor._extract_title(content, "my_book.txt")
    assert title == "my book"  # After cleaning


def test_extract_author_author_colon(extractor: TxtMetadataExtractor) -> None:
    """Test _extract_author with author: pattern (covers lines 134-141)."""
    content = "Author: Test Author\nContent"
    author = extractor._extract_author(content)
    assert author == "Test Author"


def test_extract_author_by_pattern(extractor: TxtMetadataExtractor) -> None:
    """Test _extract_author with 'by' pattern (covers lines 134-141)."""
    content = "By Test Author\nContent"
    author = extractor._extract_author(content)
    assert author == "Test Author"


def test_extract_author_written_by(extractor: TxtMetadataExtractor) -> None:
    """Test _extract_author with 'written by' pattern (covers lines 134-141)."""
    content = "Written by: Test Author\nContent"
    author = extractor._extract_author(content)
    assert author == "Test Author"


def test_extract_author_too_long(extractor: TxtMetadataExtractor) -> None:
    """Test _extract_author with author too long (covers lines 138-139)."""
    # Create an author longer than 100 characters
    long_author = "A" * 150
    content = f"Author: {long_author}\nContent"
    author = extractor._extract_author(content)
    # Should return Unknown
    assert author == "Unknown"


def test_extract_author_no_match(extractor: TxtMetadataExtractor) -> None:
    """Test _extract_author with no match (covers lines 134-141)."""
    content = "No author pattern here\nContent"
    author = extractor._extract_author(content)
    assert author == "Unknown"


def test_extract_from_filename(extractor: TxtMetadataExtractor) -> None:
    """Test _extract_from_filename (covers lines 160-161)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        file_path = Path(tmp.name)

    try:
        metadata = extractor._extract_from_filename(file_path, "my_book.txt")
        assert metadata.title == "my book"  # After cleaning
        assert metadata.author == "Unknown"
    finally:
        file_path.unlink()


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("my_book.txt", "my book"),
        ("123-my_book.txt", "my book"),  # Leading numbers removed
        ("my-book.txt", "my book"),  # Dashes replaced
        ("my_book.txt", "my book"),  # Underscores replaced  # noqa: PT014
        ("book", "book"),
    ],
)
def test_extract_title_from_filename(
    extractor: TxtMetadataExtractor, filename: str, expected: str
) -> None:
    """Test _extract_title_from_filename (covers lines 177-183)."""
    result = extractor._extract_title_from_filename(filename)
    assert result == expected


def test_extract_title_from_filename_empty_stem(
    extractor: TxtMetadataExtractor,
) -> None:
    """Test _extract_title_from_filename with empty stem (covers lines 182-183)."""
    result = extractor._extract_title_from_filename(".txt")
    assert result == ".txt"
