# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for filename metadata extractor to achieve 100% coverage."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from fundamental.services.metadata_extractors.filename import FilenameMetadataExtractor


@pytest.fixture
def extractor() -> FilenameMetadataExtractor:
    """Create FilenameMetadataExtractor instance."""
    return FilenameMetadataExtractor()


@pytest.mark.parametrize(
    ("file_format", "expected"),
    [
        ("epub", True),
        ("pdf", True),
        ("mobi", True),
        ("", True),
        ("txt", True),
        (".epub", True),
        ("EPUB", True),
    ],
)
def test_can_handle(
    extractor: FilenameMetadataExtractor, file_format: str, expected: bool
) -> None:
    """Test can_handle returns True for all formats (covers line 39-41)."""
    assert extractor.can_handle(file_format) == expected


@pytest.mark.parametrize(
    ("filename", "expected_title", "expected_author"),
    [
        ("Author - Title.epub", "Title", "Author"),
        ("Author - Title: Subtitle.pdf", "Title: Subtitle", "Author"),
        ("Author - Title - Extra.mobi", "Title - Extra", "Author"),
        ("Just Title.txt", "Just Title", "Unknown"),
        ("Author - .epub", "Author - ", "Author"),
        (" - Title.epub", "Title", "Unknown"),
    ],
)
def test_extract_author_title_pattern(
    extractor: FilenameMetadataExtractor,
    filename: str,
    expected_title: str,
    expected_author: str,
) -> None:
    """Test extract parses author-title pattern (covers lines 43-71)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / filename
        file_path.write_text("dummy content")

        metadata = extractor.extract(file_path, filename)

        assert metadata.title == expected_title
        assert metadata.author == expected_author


def test_extract_empty_stem(
    extractor: FilenameMetadataExtractor,
) -> None:
    """Test extract handles empty/whitespace stem (covers lines 51-53)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test with a file that has whitespace-only stem (no extension)
        # This tests the "not stem or stem.strip() == ''" condition
        file_path = Path(tmpdir) / "   "
        file_path.write_text("dummy")

        metadata = extractor.extract(file_path, "   ")

        # When stem is whitespace-only, it should return Unknown
        assert metadata.title == "Unknown"
        assert metadata.author == "Unknown"


def test_extract_whitespace_stem(
    extractor: FilenameMetadataExtractor,
) -> None:
    """Test extract handles whitespace-only stem (covers line 52)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "   .epub"
        file_path.write_text("dummy")

        metadata = extractor.extract(file_path, "   .epub")

        assert metadata.title == "Unknown"
        assert metadata.author == "Unknown"


def test_extract_no_separator(
    extractor: FilenameMetadataExtractor,
) -> None:
    """Test extract handles filename without separator (covers lines 66-69)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "JustTitle.epub"
        file_path.write_text("dummy")

        metadata = extractor.extract(file_path, "JustTitle.epub")

        assert metadata.title == "JustTitle"
        assert metadata.author == "Unknown"


def test_extract_empty_author_after_split(
    extractor: FilenameMetadataExtractor,
) -> None:
    """Test extract handles empty author after split (covers lines 60-62)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / " - Title.epub"
        file_path.write_text("dummy")

        metadata = extractor.extract(file_path, " - Title.epub")

        assert metadata.title == "Title"
        assert metadata.author == "Unknown"


def test_extract_empty_title_after_split(
    extractor: FilenameMetadataExtractor,
) -> None:
    """Test extract handles empty title after split (covers lines 63-65)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "Author - .epub"
        file_path.write_text("dummy")

        metadata = extractor.extract(file_path, "Author - .epub")

        # When title is empty after split, it uses the whole stem
        assert metadata.title == "Author - "  # stem includes trailing space
        assert metadata.author == "Author"
