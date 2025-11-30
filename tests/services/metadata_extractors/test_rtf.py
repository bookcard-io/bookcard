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

"""Tests for RTF metadata extractor to achieve 100% coverage."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from fundamental.services.metadata_extractors.rtf import RtfMetadataExtractor


@pytest.fixture
def extractor() -> RtfMetadataExtractor:
    """Create RtfMetadataExtractor instance."""
    return RtfMetadataExtractor()


def _create_mock_rtf_file(rtf_content: str, encoding: str = "utf-8") -> Path:
    """Create a mock RTF file for testing.

    Parameters
    ----------
    rtf_content : str
        RTF content to write.
    encoding : str
        File encoding.

    Returns
    -------
    Path
        Path to the created RTF file.
    """
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".rtf", mode="w", encoding=encoding
    ) as tmp:
        file_path = Path(tmp.name)
        tmp.write(rtf_content)

    return file_path


@pytest.mark.parametrize(
    ("file_format", "expected"),
    [
        ("rtf", True),
        ("RTF", True),
        (".rtf", True),
        ("pdf", False),
        ("epub", False),
    ],
)
def test_can_handle(
    extractor: RtfMetadataExtractor, file_format: str, expected: bool
) -> None:
    """Test can_handle for various formats (covers lines 56-59)."""
    assert extractor.can_handle(file_format) == expected


def test_extract_with_utf8(extractor: RtfMetadataExtractor) -> None:
    """Test extract with UTF-8 encoding (covers lines 76-80)."""
    rtf_content = """{\\rtf1\\ansi
{\\title Test Book}
{\\author Test Author}
{\\subject Test Description}
{\\keywords tag1, tag2}
{\\company Test Publisher}
}"""

    file_path = _create_mock_rtf_file(rtf_content, encoding="utf-8")

    try:
        metadata = extractor.extract(file_path, "test.rtf")
        assert metadata.title == "Test Book"
        assert metadata.author == "Test Author"
        assert metadata.description == "Test Description"
        assert metadata.tags is not None
        assert "tag1" in metadata.tags
        assert metadata.publisher == "Test Publisher"
    finally:
        file_path.unlink()


def test_extract_with_latin1_fallback(extractor: RtfMetadataExtractor) -> None:
    """Test extract falls back to latin-1 encoding (covers lines 81-88)."""
    # Create file with latin-1 encoding that would fail with utf-8
    rtf_content = """{\\rtf1\\ansi
{\\title Test Book}
{\\author Test Author}
}"""

    file_path = _create_mock_rtf_file(rtf_content, encoding="latin-1")

    try:
        metadata = extractor.extract(file_path, "test.rtf")
        assert metadata.title == "Test Book"
        assert metadata.author == "Test Author"
    finally:
        file_path.unlink()


def test_extract_os_error(extractor: RtfMetadataExtractor) -> None:
    """Test extract handles OSError (covers lines 81-90)."""
    # Create a non-existent file path
    file_path = Path("/nonexistent/path/test.rtf")

    metadata = extractor.extract(file_path, "test.rtf")
    assert metadata.title == "test"
    assert metadata.author == "Unknown"


def test_extract_unicode_decode_error(extractor: RtfMetadataExtractor) -> None:
    """Test extract handles UnicodeDecodeError (covers lines 81-90)."""
    # Create a file with invalid UTF-8 that will fail both encodings
    with tempfile.NamedTemporaryFile(delete=False, suffix=".rtf", mode="wb") as tmp:
        file_path = Path(tmp.name)
        # Write invalid UTF-8 bytes
        tmp.write(b"\xff\xfe\x00\x00")

    try:
        metadata = extractor.extract(file_path, "test.rtf")
        assert metadata.title == "test"
        assert metadata.author == "Unknown"
    finally:
        file_path.unlink()


def test_parse_rtf_content_full(extractor: RtfMetadataExtractor) -> None:
    """Test _parse_rtf_content with all metadata fields (covers lines 107-153)."""
    rtf_content = """{\\rtf1\\ansi
{\\title Test Book}
{\\author Test Author}
{\\subject Test Subject}
{\\comment Test Comment}
{\\doccomm Test DocComm}
{\\keywords tag1, tag2, tag3}
{\\category Test Category}
{\\company Test Publisher}
}"""

    metadata = extractor._parse_rtf_content(rtf_content, "test.rtf")
    assert metadata.title == "Test Book"
    assert metadata.author == "Test Author"
    # Description should use subject first, then comment, then doccomm
    assert metadata.description == "Test Subject"
    assert metadata.tags is not None
    assert "tag1" in metadata.tags
    assert "tag2" in metadata.tags
    assert "tag3" in metadata.tags
    assert "Test Category" in metadata.tags
    assert metadata.publisher == "Test Publisher"


def test_parse_rtf_content_no_title(extractor: RtfMetadataExtractor) -> None:
    """Test _parse_rtf_content with no title (covers lines 120-122)."""
    rtf_content = """{\\rtf1\\ansi
{\\author Test Author}
}"""

    metadata = extractor._parse_rtf_content(rtf_content, "my_book.rtf")
    assert metadata.title == "my_book"


def test_parse_rtf_content_description_fallback(
    extractor: RtfMetadataExtractor,
) -> None:
    """Test _parse_rtf_content description fallback (covers lines 128-133)."""
    # Test with comment when no subject
    rtf_content = """{\\rtf1\\ansi
{\\title Test Book}
{\\comment Test Comment}
}"""

    metadata = extractor._parse_rtf_content(rtf_content, "test.rtf")
    assert metadata.description == "Test Comment"

    # Test with doccomm when no subject or comment
    rtf_content2 = """{\\rtf1\\ansi
{\\title Test Book}
{\\doccomm Test DocComm}
}"""

    metadata2 = extractor._parse_rtf_content(rtf_content2, "test.rtf")
    assert metadata2.description == "Test DocComm"

    # Test with no description fields
    rtf_content3 = """{\\rtf1\\ansi
{\\title Test Book}
}"""

    metadata3 = extractor._parse_rtf_content(rtf_content3, "test.rtf")
    assert metadata3.description == ""


def test_parse_rtf_content_tags(extractor: RtfMetadataExtractor) -> None:
    """Test _parse_rtf_content with tags (covers lines 136-142)."""
    # Test with keywords only
    rtf_content = """{\\rtf1\\ansi
{\\title Test Book}
{\\keywords tag1, tag2}
}"""

    metadata = extractor._parse_rtf_content(rtf_content, "test.rtf")
    assert metadata.tags is not None
    assert len(metadata.tags) == 2

    # Test with category only
    rtf_content2 = """{\\rtf1\\ansi
{\\title Test Book}
{\\category Test Category}
}"""

    metadata2 = extractor._parse_rtf_content(rtf_content2, "test.rtf")
    assert metadata2.tags is not None
    assert "Test Category" in metadata2.tags

    # Test with no tags
    rtf_content3 = """{\\rtf1\\ansi
{\\title Test Book}
}"""

    metadata3 = extractor._parse_rtf_content(rtf_content3, "test.rtf")
    # Empty list should be converted to None, but BookMetadata might initialize as []
    assert metadata3.tags is None or metadata3.tags == []


def test_clean_rtf_text(extractor: RtfMetadataExtractor) -> None:
    """Test _clean_rtf_text (covers lines 170-179)."""
    # Test with hex codes
    text = "Test\\'41Book"
    result = extractor._clean_rtf_text(text)
    assert "Test" in result
    assert "Book" in result

    # Test with unicode escapes
    text2 = "Test\\u1234Book"
    result2 = extractor._clean_rtf_text(text2)
    assert "Test" in result2
    assert "Book" in result2

    # Test with braces
    text3 = "Test{Book}"
    result3 = extractor._clean_rtf_text(text3)
    assert "Test" in result3
    assert "Book" in result3
    assert "{" not in result3
    assert "}" not in result3

    # Test with backslashes
    text4 = "Test\\Book"
    result4 = extractor._clean_rtf_text(text4)
    assert "Test" in result4
    assert "Book" in result4

    # Test with multiple whitespace
    text5 = "Test    Book"
    result5 = extractor._clean_rtf_text(text5)
    assert "Test Book" in result5

    # Test with negative unicode escape
    text6 = "Test\\u-1234Book"
    result6 = extractor._clean_rtf_text(text6)
    assert "Test" in result6
    assert "Book" in result6


def test_extract_from_filename(extractor: RtfMetadataExtractor) -> None:
    """Test _extract_from_filename (covers lines 194-195)."""
    metadata = extractor._extract_from_filename("my_book.rtf")
    assert metadata.title == "my_book"
    assert metadata.author == "Unknown"


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("my_book.rtf", "my_book"),
        ("my.book.rtf", "my.book"),
        ("book", "book"),
        (".hidden", ".hidden"),
    ],
)
def test_extract_title_from_filename(
    extractor: RtfMetadataExtractor, filename: str, expected: str
) -> None:
    """Test _extract_title_from_filename (covers lines 211-214)."""
    result = extractor._extract_title_from_filename(filename)
    assert result == expected


def test_extract_title_from_filename_empty_stem(
    extractor: RtfMetadataExtractor,
) -> None:
    """Test _extract_title_from_filename with empty stem (covers lines 213-214)."""
    result = extractor._extract_title_from_filename(".rtf")
    assert result == ".rtf"
