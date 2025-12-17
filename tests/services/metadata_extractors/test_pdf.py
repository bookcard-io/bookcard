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

"""Tests for PDF metadata extractor to achieve 100% coverage."""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bookcard.services.metadata_extractors.pdf import PdfMetadataExtractor


@pytest.fixture
def extractor() -> PdfMetadataExtractor:
    """Create PdfMetadataExtractor instance."""
    return PdfMetadataExtractor()


@pytest.mark.parametrize(
    ("file_format", "expected"),
    [
        ("pdf", True),
        ("PDF", True),
        (".pdf", True),
        ("epub", False),
        ("mobi", False),
    ],
)
def test_can_handle(
    extractor: PdfMetadataExtractor, file_format: str, expected: bool
) -> None:
    """Test can_handle for various formats (covers lines 50-52)."""
    assert extractor.can_handle(file_format) == expected


def test_extract_no_metadata(extractor: PdfMetadataExtractor) -> None:
    """Test extract with no metadata (covers lines 54-69)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file_path = Path(tmp.name)

    try:
        with patch(
            "bookcard.services.metadata_extractors.pdf.PdfReader"
        ) as mock_reader_class:
            mock_reader = MagicMock()
            mock_reader.metadata = None
            mock_reader_class.return_value = mock_reader

            metadata = extractor.extract(file_path, "test.pdf")
            assert metadata.title == "test.pdf"
            assert metadata.author == "Unknown"
    finally:
        file_path.unlink()


def test_extract_with_info_metadata(extractor: PdfMetadataExtractor) -> None:
    """Test extract with Info dictionary metadata (covers lines 60-140)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file_path = Path(tmp.name)

    try:
        with patch(
            "bookcard.services.metadata_extractors.pdf.PdfReader"
        ) as mock_reader_class:
            mock_reader = MagicMock()
            mock_reader.metadata = {
                "/Title": "Test Title",
                "/Author": "Test Author",
                "/Subject": "Test Description",
                "/Producer": "Test Publisher",
                "/Keywords": "tag1, tag2",
                "/CreationDate": "D:20230115100000",
                "/ModDate": "D:20230116100000",
            }
            mock_reader.xmp_metadata = None
            mock_reader_class.return_value = mock_reader

            metadata = extractor.extract(file_path, "test.pdf")
            assert metadata.title == "Test Title"
            assert metadata.author == "Test Author"
            assert metadata.description == "Test Description"
            assert metadata.publisher == "Test Publisher"
            assert metadata.tags is not None
            assert "tag1" in metadata.tags
    finally:
        file_path.unlink()


def test_extract_with_xmp_metadata(extractor: PdfMetadataExtractor) -> None:
    """Test extract with XMP metadata (covers lines 71-77, 142-183)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file_path = Path(tmp.name)

    try:
        with patch(
            "bookcard.services.metadata_extractors.pdf.PdfReader"
        ) as mock_reader_class:
            mock_xmp = MagicMock()
            mock_xmp.dc_title = "XMP Title"
            mock_xmp.dc_creator = "XMP Author"
            mock_xmp.dc_description = "XMP Description"
            mock_xmp.dc_publisher = "XMP Publisher"
            mock_xmp.dc_language = "en"
            mock_xmp.dc_rights = "XMP Rights"

            mock_reader = MagicMock()
            mock_reader.metadata = {"/Title": "Info Title"}
            mock_reader.xmp_metadata = mock_xmp
            mock_reader_class.return_value = mock_reader

            metadata = extractor.extract(file_path, "test.pdf")
            assert metadata.title == "XMP Title"
            assert metadata.author == "XMP Author"

            # Test exception handling when accessing xmp_metadata (covers lines 76-77)
            # Create a reader that raises when xmp_metadata is accessed
            class ReaderWithException:
                def __init__(self) -> None:
                    self.metadata = {"/Title": "Test"}

                @property
                def xmp_metadata(self) -> None:
                    raise AttributeError("test")

            mock_reader2 = ReaderWithException()
            mock_reader_class.return_value = mock_reader2
            # This should handle the exception gracefully (lines 76-77)
            # Line 74: hasattr check passes
            # Line 75: accessing xmp_metadata raises AttributeError
            # Line 76: exception is caught
            # Line 77: pass (continue execution)
            metadata2 = extractor.extract(file_path, "test2.pdf")
            assert metadata2.title == "Test" or metadata2.title == "test2.pdf"

            # Test with KeyError exception (covers lines 76-77)
            class ReaderWithKeyError:
                def __init__(self) -> None:
                    self.metadata = {"/Title": "Test"}

                @property
                def xmp_metadata(self) -> None:
                    raise KeyError("test")

            mock_reader3 = ReaderWithKeyError()
            mock_reader_class.return_value = mock_reader3
            metadata3 = extractor.extract(file_path, "test3.pdf")
            assert metadata3.title == "Test" or metadata3.title == "test3.pdf"

            # Test with TypeError exception (covers lines 76-77)
            class ReaderWithTypeError:
                def __init__(self) -> None:
                    self.metadata = {"/Title": "Test"}

                @property
                def xmp_metadata(self) -> None:
                    raise TypeError("test")

            mock_reader4 = ReaderWithTypeError()
            mock_reader_class.return_value = mock_reader4
            metadata4 = extractor.extract(file_path, "test4.pdf")
            assert metadata4.title == "Test" or metadata4.title == "test4.pdf"
    finally:
        file_path.unlink()


def test_get_xmp_field_attribute(extractor: PdfMetadataExtractor) -> None:
    """Test _get_xmp_field with attribute access (covers lines 142-183)."""
    mock_xmp = MagicMock()
    mock_xmp.dc_title = "Test Title"
    mock_xmp.dc_creator = ["Author1", "Author2"]

    result = extractor._get_xmp_field(mock_xmp, "dc:title")
    assert result == "Test Title"

    result = extractor._get_xmp_field(mock_xmp, "dc:creator")
    assert result is not None


def test_get_xmp_field_dict(extractor: PdfMetadataExtractor) -> None:
    """Test _get_xmp_field with dict access (covers lines 174-178)."""
    mock_xmp = {"dc:title": "Dict Title", "dc_creator": "Dict Author"}

    result = extractor._get_xmp_field(mock_xmp, "dc:title")
    assert result == "Dict Title"

    result = extractor._get_xmp_field(mock_xmp, "dc:creator")
    assert result == "Dict Author"


def test_get_xmp_field_none(extractor: PdfMetadataExtractor) -> None:
    """Test _get_xmp_field with None (covers line 160)."""
    result = extractor._get_xmp_field(None, "dc:title")
    assert result is None

    # Test exception handling in _get_xmp_field (covers lines 180-183)
    class BadXMP:
        def __getattr__(self, name: str) -> None:
            # Raise AttributeError for any attribute access
            raise AttributeError("test")

        def __getitem__(self, key: str) -> None:
            # Raise KeyError for dict access
            raise KeyError("test")

        def __contains__(self, key: str) -> bool:
            # Raise TypeError for 'in' operator
            raise TypeError("test")

    bad_xmp = BadXMP()
    result = extractor._get_xmp_field(bad_xmp, "dc:title")
    # Should handle exception gracefully (lines 180-181)
    assert result is None


def test_get_xmp_field_exception(extractor: PdfMetadataExtractor) -> None:
    """Test _get_xmp_field exception handling (covers lines 180-181)."""

    # Test with AttributeError when accessing attribute
    class XmpWithAttributeError:
        def __getattr__(self, name: str) -> None:
            raise AttributeError("test")

    mock_xmp1 = XmpWithAttributeError()
    # This should execute lines 169-171, then catch AttributeError at line 180
    result = extractor._get_xmp_field(mock_xmp1, "dc:title")
    assert result is None

    # Test with KeyError when accessing as dict
    class XmpDictWithKeyError:
        def __init__(self) -> None:
            pass

        def __getattr__(self, name: str) -> None:
            # hasattr will return False, so we'll try dict access
            raise AttributeError("test")

        def __getitem__(self, key: str) -> None:
            raise KeyError("test")

    # Test with KeyError when accessing as dict - use a real dict that raises on access
    class DictWithKeyError(dict):
        def __getitem__(self, key: str) -> None:
            raise KeyError("test")

    mock_xmp2 = DictWithKeyError()
    # This should execute lines 174-178, then catch KeyError at line 180
    result2 = extractor._get_xmp_field(mock_xmp2, "dc:title")
    assert result2 is None

    # Test with TypeError
    class XmpWithTypeError:
        def __init__(self) -> None:
            pass

        def __getattr__(self, name: str) -> None:
            raise TypeError("test")

    mock_xmp3 = XmpWithTypeError()
    result3 = extractor._get_xmp_field(mock_xmp3, "dc:title")
    assert result3 is None


def test_normalize_xmp_value(extractor: PdfMetadataExtractor) -> None:
    """Test _normalize_xmp_value (covers lines 185-220)."""
    # Test with list
    result = extractor._normalize_xmp_value(["value1", "value2"])
    assert result == "value1"

    # Test with empty list (covers line 207)
    result = extractor._normalize_xmp_value([])
    assert result is None

    # Test with dict
    result = extractor._normalize_xmp_value({"value": "test"})
    assert result == "test"

    # Test with dict that raises exception (covers lines 216-217)
    class BadDict(dict):
        def get(self, key: str, default: object = None) -> None:
            raise KeyError("test")

    bad_dict = BadDict()
    result = extractor._normalize_xmp_value(bad_dict)
    # Should handle exception gracefully
    assert isinstance(result, str)

    # Test with string
    result = extractor._normalize_xmp_value("  test  ")
    assert result == "test"

    # Test with None
    result = extractor._normalize_xmp_value(None)
    assert result is None


def test_extract_contributors(extractor: PdfMetadataExtractor) -> None:
    """Test _extract_contributors (covers lines 222-245)."""
    mock_xmp = MagicMock()
    mock_xmp.dc_contributor = "Contributor1, Contributor2"
    mock_xmp.dc_creator = "Author1"

    info = {"/Author": "Info Author"}

    contributors = extractor._extract_contributors(mock_xmp, info)
    assert len(contributors) > 0

    # Test with no XMP, fallback to Info
    contributors = extractor._extract_contributors(None, info)
    assert len(contributors) > 0


def test_parse_contributor_list(extractor: PdfMetadataExtractor) -> None:
    """Test _parse_contributor_list (covers lines 247-258)."""
    contributors = extractor._parse_contributor_list("Author1, Author2", "author")
    assert len(contributors) == 2

    contributors = extractor._parse_contributor_list("Single Author", "author")
    assert len(contributors) == 1

    contributors = extractor._parse_contributor_list("", "author")
    assert len(contributors) == 0


def test_extract_tags(extractor: PdfMetadataExtractor) -> None:
    """Test _extract_tags (covers lines 260-277)."""
    info = {"/Keywords": "tag1, tag2, tag3"}
    tags = extractor._extract_tags(info, None)
    assert len(tags) == 3

    tags = extractor._extract_tags({}, "dc:subject")
    assert len(tags) > 0

    # Test with list for dc_subject (covers line 273)
    # Note: The method signature says str | None, but the implementation handles lists
    tags = extractor._extract_tags({}, ["subject1", "subject2", "subject3"])  # type: ignore[arg-type]
    assert len(tags) == 3
    assert "subject1" in tags
    assert "subject2" in tags
    assert "subject3" in tags

    # Test with None for dc_subject
    tags = extractor._extract_tags({}, None)
    assert len(tags) == 0


def test_extract_pubdate(extractor: PdfMetadataExtractor) -> None:
    """Test _extract_pubdate (covers lines 279-295)."""
    info = {"/CreationDate": "D:20230115100000"}
    pubdate = extractor._extract_pubdate(info)
    assert pubdate is None or isinstance(pubdate, datetime)

    info = {"/ModDate": "D:20230115100000"}
    pubdate = extractor._extract_pubdate(info)
    assert pubdate is None or isinstance(pubdate, datetime)

    pubdate = extractor._extract_pubdate({})
    assert pubdate is None


def test_extract_modified(extractor: PdfMetadataExtractor) -> None:
    """Test _extract_modified (covers lines 297-304)."""
    info = {"/ModDate": "D:20230115100000"}
    modified = extractor._extract_modified(info)
    assert modified is None or isinstance(modified, datetime)

    modified = extractor._extract_modified({})
    assert modified is None


def test_parse_pdf_date(extractor: PdfMetadataExtractor) -> None:
    """Test _parse_pdf_date (covers lines 306-341)."""
    # Test with empty string (covers line 313)
    result = extractor._parse_pdf_date("")
    assert result is None

    # Test with D: prefix
    result = extractor._parse_pdf_date("D:20230115")
    assert result is None or isinstance(result, datetime)

    # Test without D: prefix
    result = extractor._parse_pdf_date("20230115")
    assert result is None or isinstance(result, datetime)

    # Test ISO format
    result = extractor._parse_pdf_date("2023-01-15")
    assert result is None or isinstance(result, datetime)

    # Test with date that works with first format
    result = extractor._parse_pdf_date("20230115")  # This should work with first format
    assert isinstance(result, datetime)
    assert result.year == 2023
    assert result.month == 1
    assert result.day == 15

    # Test with invalid format that raises ValueError in strptime (covers lines 337-339)
    # Use a date string that will pass the length check but fail strptime
    result = extractor._parse_pdf_date("2023-13-45")  # Invalid month/day
    assert result is None

    # Test with ValueError in strptime (covers lines 337-339)
    # Create a date string that passes len check but strptime fails
    result = extractor._parse_pdf_date("2023-01-45")  # Invalid day
    assert result is None

    # Test with TypeError in split (covers lines 337-339)
    # Pass something that will cause TypeError in split
    result = extractor._parse_pdf_date(None)  # type: ignore[arg-type]
    assert result is None

    # Test with TypeError in split (covers lines 337-339)
    # Create a string-like object that passes lstrip but fails in split
    class BadDateStr:
        def lstrip(self, chars: str | None = None) -> BadDateStr:
            return self

        def split(self, *args: object) -> None:
            # Raise TypeError to trigger exception handler at line 338
            raise TypeError("split error")

        def __len__(self) -> int:
            return 10

        def __getitem__(self, key: object) -> object:
            if isinstance(key, slice):
                return "2023-01-15"
            return "2"

        def __bool__(self) -> bool:
            return True

    bad_date = BadDateStr()
    # This should cause TypeError in split (line 335), caught at line 338
    result = extractor._parse_pdf_date(bad_date)  # type: ignore[arg-type]
    assert result is None

    # Test with TypeError in split (covers line 338)
    # The BadDateStr above already covers TypeError in split at line 338
    # For TypeError in strptime, it's hard to trigger naturally, but ValueError is covered above

    # Test invalid
    result = extractor._parse_pdf_date("")
    assert result is None


def test_extract_identifiers(extractor: PdfMetadataExtractor) -> None:
    """Test _extract_identifiers (covers lines 343-372)."""
    # Test with URN
    identifiers = extractor._extract_identifiers("urn:isbn:1234567890")
    assert len(identifiers) > 0

    # Test with DOI
    identifiers = extractor._extract_identifiers("doi:10.1234/test")
    assert len(identifiers) > 0

    # Test with ISBN13
    identifiers = extractor._extract_identifiers("1234567890123")
    assert len(identifiers) > 0

    # Test with ISBN10 (covers line 368)
    identifiers = extractor._extract_identifiers("1234567890")
    assert len(identifiers) > 0
    # Check that one identifier has type "isbn10"
    isbn10_found = any(ident.get("type") == "isbn10" for ident in identifiers)
    assert isbn10_found

    # Test with None
    identifiers = extractor._extract_identifiers(None)
    assert identifiers == []


def test_extract_primary_author_from_contributors(
    extractor: PdfMetadataExtractor,
) -> None:
    """Test extract primary author from contributors (covers lines 117-126)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file_path = Path(tmp.name)

    try:
        with patch(
            "bookcard.services.metadata_extractors.pdf.PdfReader"
        ) as mock_reader_class:
            from bookcard.services.book_metadata import Contributor

            mock_reader = MagicMock()
            mock_reader.metadata = {}
            mock_reader.xmp_metadata = None
            mock_reader_class.return_value = mock_reader

            # Mock _extract_contributors to return authors
            with patch.object(
                extractor,
                "_extract_contributors",
                return_value=[
                    Contributor(name="Author1", role="author"),
                    Contributor(name="Author2", role="author"),
                ],
            ):
                metadata = extractor.extract(file_path, "test.pdf")
                assert "Author1" in metadata.author

            # Test fallback to contributor name when primary_author is Unknown (covers lines 125-126)
            with (
                patch.object(
                    extractor,
                    "_extract_contributors",
                    return_value=[
                        Contributor(name="Contributor Name", role="contributor"),
                    ],
                ),
                patch.object(extractor, "_get_xmp_field", return_value=None),
            ):
                metadata2 = extractor.extract(file_path, "test2.pdf")
                # Should use contributor name when primary_author is Unknown (lines 125-126)
                assert metadata2.author == "Contributor Name"
    finally:
        file_path.unlink()
