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

"""Tests for OPF service to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from lxml import etree  # type: ignore[import]

from bookcard.models.core import Book
from bookcard.repositories.models import BookWithFullRelations
from bookcard.services.opf_service import OpfMetadataResult, OpfService


@pytest.fixture
def book() -> Book:
    """Create a test book."""
    return Book(
        id=1,
        title="Test Book",
        timestamp=datetime.now(UTC),
        pubdate=datetime(2020, 1, 1, tzinfo=UTC),
        uuid="test-uuid-123",
        has_cover=False,
        path="Author Name/Test Book (1)",
    )


@pytest.fixture
def book_with_full_metadata(book: Book) -> BookWithFullRelations:
    """Create a test book with full metadata."""
    book.series_index = 1.5  # Set series_index on book
    return BookWithFullRelations(
        book=book,
        authors=["Author One", "Author Two"],
        series="Test Series",
        series_id=1,
        tags=["Fiction", "Science Fiction"],
        identifiers=[
            {"type": "isbn", "val": "978-1234567890"},
            {"type": "asin", "val": "B01234567"},
        ],
        description="A test book description",
        publisher="Test Publisher",
        publisher_id=1,
        languages=["en", "fr"],
        language_ids=[1, 2],
        rating=4,
        rating_id=1,
        formats=[{"format": "EPUB", "name": "test.epub", "size": 1000}],
    )


@pytest.fixture
def book_minimal(book: Book) -> BookWithFullRelations:
    """Create a test book with minimal metadata."""
    return BookWithFullRelations(
        book=book,
        authors=[],
        series=None,
        series_id=None,
        tags=[],
        identifiers=[],
        description=None,
        publisher=None,
        publisher_id=None,
        languages=[],
        language_ids=[],
        rating=None,
        rating_id=None,
        formats=[],
    )


def test_generate_opf_full_metadata(
    book_with_full_metadata: BookWithFullRelations,
) -> None:
    """Test generate_opf with full metadata (covers lines 81-116)."""
    service = OpfService()
    result = service.generate_opf(book_with_full_metadata)

    assert isinstance(result, OpfMetadataResult)
    assert result.xml_content is not None
    assert result.filename is not None
    assert "test-uuid-123" in result.xml_content
    assert "Test Book" in result.xml_content
    assert "Author One" in result.xml_content
    assert "Author Two" in result.xml_content
    assert "Test Publisher" in result.xml_content
    assert "Test Series" in result.xml_content
    assert "Fiction" in result.xml_content
    assert "Science Fiction" in result.xml_content
    assert "978-1234567890" in result.xml_content
    assert "en" in result.xml_content
    assert "fr" in result.xml_content


def test_generate_opf_minimal_metadata(book_minimal: BookWithFullRelations) -> None:
    """Test generate_opf with minimal metadata."""
    service = OpfService()
    result = service.generate_opf(book_minimal)

    assert isinstance(result, OpfMetadataResult)
    assert result.xml_content is not None
    assert result.filename is not None
    assert "test-uuid-123" in result.xml_content
    assert "Test Book" in result.xml_content


def test_create_package_element() -> None:
    """Test _create_package_element (covers lines 126-135)."""
    service = OpfService()
    package = service._create_package_element()

    assert package.tag == "package"
    assert package.get("version") == "3.0"
    assert package.get("unique_identifier") == "bookid"
    assert package.nsmap is not None


def test_add_identifier(book_with_full_metadata: BookWithFullRelations) -> None:
    """Test _add_identifier (covers lines 149-154)."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_with_full_metadata)
    service._add_identifier(metadata, structured)

    identifiers = metadata.findall(".//{http://purl.org/dc/elements/1.1/}identifier")
    assert len(identifiers) == 1
    assert identifiers[0].get("id") == "bookid"
    assert identifiers[0].text == structured.uuid


def test_add_title_with_title(book_with_full_metadata: BookWithFullRelations) -> None:
    """Test _add_title with title (covers lines 168-170)."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_with_full_metadata)
    service._add_title(metadata, structured)

    titles = metadata.findall(".//{http://purl.org/dc/elements/1.1/}title")
    assert len(titles) == 1
    assert titles[0].text == structured.title


def test_add_title_without_title(book_minimal: BookWithFullRelations) -> None:
    """Test _add_title without title."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_minimal)
    service._add_title(metadata, structured)

    titles = metadata.findall(".//{http://purl.org/dc/elements/1.1/}title")
    assert len(titles) == 1  # Title should still be added even if empty


def test_add_authors(book_with_full_metadata: BookWithFullRelations) -> None:
    """Test _add_authors (covers lines 184-186)."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_with_full_metadata)
    service._add_authors(metadata, structured)

    creators = metadata.findall(".//{http://purl.org/dc/elements/1.1/}creator")
    assert len(creators) == 2
    assert creators[0].text == "Author One"
    assert creators[1].text == "Author Two"


def test_add_publisher_with_publisher(
    book_with_full_metadata: BookWithFullRelations,
) -> None:
    """Test _add_publisher with publisher (covers lines 200-202)."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_with_full_metadata)
    service._add_publisher(metadata, structured)

    publishers = metadata.findall(".//{http://purl.org/dc/elements/1.1/}publisher")
    assert len(publishers) == 1
    assert publishers[0].text == "Test Publisher"


def test_add_publisher_without_publisher(book_minimal: BookWithFullRelations) -> None:
    """Test _add_publisher without publisher."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_minimal)
    service._add_publisher(metadata, structured)

    publishers = metadata.findall(".//{http://purl.org/dc/elements/1.1/}publisher")
    assert len(publishers) == 0


def test_add_publication_date(book_with_full_metadata: BookWithFullRelations) -> None:
    """Test _add_publication_date (covers lines 216-223)."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_with_full_metadata)
    service._add_publication_date(metadata, structured)

    dates = metadata.findall(".//{http://purl.org/dc/terms/}date")
    assert len(dates) == 1
    assert dates[0].get("event") == "publication"
    assert dates[0].text == "2020-01-01"  # Date part only


def test_add_publication_date_with_timestamp(book: Book) -> None:
    """Test _add_publication_date with timestamp containing T."""
    book_with_date = BookWithFullRelations(
        book=book,
        authors=[],
        series=None,
        series_id=None,
        tags=[],
        identifiers=[],
        description=None,
        publisher=None,
        publisher_id=None,
        languages=[],
        language_ids=[],
        rating=None,
        rating_id=None,
        formats=[],
    )
    book_with_date.book.pubdate = datetime(2020, 1, 1, 12, 30, 45, tzinfo=UTC)

    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_with_date)
    service._add_publication_date(metadata, structured)

    dates = metadata.findall(".//{http://purl.org/dc/terms/}date")
    assert len(dates) == 1
    # Should extract date part only
    assert "T" not in dates[0].text or dates[0].text.split("T")[0] == "2020-01-01"


def test_add_description_with_description(
    book_with_full_metadata: BookWithFullRelations,
) -> None:
    """Test _add_description with description (covers lines 237-239)."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_with_full_metadata)
    service._add_description(metadata, structured)

    descriptions = metadata.findall(".//{http://purl.org/dc/elements/1.1/}description")
    assert len(descriptions) == 1
    assert descriptions[0].text == "A test book description"


def test_add_description_without_description(
    book_minimal: BookWithFullRelations,
) -> None:
    """Test _add_description without description."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_minimal)
    service._add_description(metadata, structured)

    descriptions = metadata.findall(".//{http://purl.org/dc/elements/1.1/}description")
    assert len(descriptions) == 0


def test_add_languages(book_with_full_metadata: BookWithFullRelations) -> None:
    """Test _add_languages (covers lines 253-255)."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_with_full_metadata)
    service._add_languages(metadata, structured)

    languages = metadata.findall(".//{http://purl.org/dc/elements/1.1/}language")
    assert len(languages) == 2
    assert languages[0].text == "en"
    assert languages[1].text == "fr"


def test_add_languages_empty(book_minimal: BookWithFullRelations) -> None:
    """Test _add_languages with empty languages."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_minimal)
    service._add_languages(metadata, structured)

    languages = metadata.findall(".//{http://purl.org/dc/elements/1.1/}language")
    assert len(languages) == 0


def test_add_identifiers(book_with_full_metadata: BookWithFullRelations) -> None:
    """Test _add_identifiers (covers lines 269-276)."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_with_full_metadata)
    service._add_identifiers(metadata, structured)

    identifiers = metadata.findall(".//{http://purl.org/dc/elements/1.1/}identifier")
    # Should have at least 2 (one isbn, one asin)
    assert len(identifiers) >= 2
    # Check for ISBN scheme
    isbn_found = False
    for id_elem in identifiers:
        if id_elem.get("scheme") == "ISBN":
            isbn_found = True
            assert "978-1234567890" in id_elem.text
    assert isbn_found


def test_add_identifiers_isbn_lowercase(book: Book) -> None:
    """Test _add_identifiers with lowercase isbn type."""
    book_with_isbn = BookWithFullRelations(
        book=book,
        authors=[],
        series=None,
        series_id=None,
        tags=[],
        identifiers=[{"type": "isbn", "val": "978-1234567890"}],
        description=None,
        publisher=None,
        publisher_id=None,
        languages=[],
        language_ids=[],
        rating=None,
        rating_id=None,
        formats=[],
    )

    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_with_isbn)
    service._add_identifiers(metadata, structured)

    identifiers = metadata.findall(".//{http://purl.org/dc/elements/1.1/}identifier")
    isbn_found = False
    for id_elem in identifiers:
        if id_elem.get("scheme") == "ISBN":
            isbn_found = True
    assert isbn_found


def test_add_identifiers_empty_val(book: Book) -> None:
    """Test _add_identifiers with empty val."""
    book_with_empty_id = BookWithFullRelations(
        book=book,
        authors=[],
        series=None,
        series_id=None,
        tags=[],
        identifiers=[{"type": "isbn", "val": ""}],
        description=None,
        publisher=None,
        publisher_id=None,
        languages=[],
        language_ids=[],
        rating=None,
        rating_id=None,
        formats=[],
    )

    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_with_empty_id)
    service._add_identifiers(metadata, structured)

    # Should not add identifier with empty val
    identifiers = metadata.findall(".//{http://purl.org/dc/elements/1.1/}identifier")
    # Only the bookid identifier should be present
    assert (
        len([id_elem for id_elem in identifiers if id_elem.get("id") != "bookid"]) == 0
    )


def test_add_series(book_with_full_metadata: BookWithFullRelations) -> None:
    """Test _add_series (covers lines 290-303)."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_with_full_metadata)
    service._add_series(metadata, structured)

    series_meta = metadata.findall('.//meta[@property="belongs-to-collection"]')
    assert len(series_meta) == 1
    assert series_meta[0].text == "Test Series"
    assert series_meta[0].get("id") == "series"

    series_index_meta = metadata.findall('.//meta[@property="group-position"]')
    assert len(series_index_meta) == 1
    assert series_index_meta[0].text == "1.5"
    assert series_index_meta[0].get("refines") == "#series"


def test_add_series_without_index(book: Book) -> None:
    """Test _add_series without series_index."""
    book.series_index = None  # Explicitly set to None
    book_with_series = BookWithFullRelations(
        book=book,
        authors=[],
        series="Test Series",
        series_id=1,
        tags=[],
        identifiers=[],
        description=None,
        publisher=None,
        publisher_id=None,
        languages=[],
        language_ids=[],
        rating=None,
        rating_id=None,
        formats=[],
    )

    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_with_series)
    service._add_series(metadata, structured)

    series_meta = metadata.findall('.//meta[@property="belongs-to-collection"]')
    assert len(series_meta) == 1
    series_index_meta = metadata.findall('.//meta[@property="group-position"]')
    assert len(series_index_meta) == 0


def test_add_series_without_series(book_minimal: BookWithFullRelations) -> None:
    """Test _add_series without series."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_minimal)
    service._add_series(metadata, structured)

    series_meta = metadata.findall('.//meta[@property="belongs-to-collection"]')
    assert len(series_meta) == 0


def test_add_tags(book_with_full_metadata: BookWithFullRelations) -> None:
    """Test _add_tags (covers lines 317-319)."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_with_full_metadata)
    service._add_tags(metadata, structured)

    subjects = metadata.findall(".//{http://purl.org/dc/elements/1.1/}subject")
    assert len(subjects) == 2
    assert subjects[0].text == "Fiction"
    assert subjects[1].text == "Science Fiction"


def test_add_tags_empty(book_minimal: BookWithFullRelations) -> None:
    """Test _add_tags with empty tags."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_minimal)
    service._add_tags(metadata, structured)

    subjects = metadata.findall(".//{http://purl.org/dc/elements/1.1/}subject")
    assert len(subjects) == 0


def test_add_rating(book_with_full_metadata: BookWithFullRelations) -> None:
    """Test _add_rating (covers lines 333-339)."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_with_full_metadata)
    service._add_rating(metadata, structured)

    rating_meta = metadata.findall('.//meta[@property="calibre:rating"]')
    assert len(rating_meta) == 1
    assert rating_meta[0].text == "4"


def test_add_rating_without_rating(book_minimal: BookWithFullRelations) -> None:
    """Test _add_rating without rating."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_minimal)
    service._add_rating(metadata, structured)

    rating_meta = metadata.findall('.//meta[@property="calibre:rating"]')
    assert len(rating_meta) == 0


def test_add_modified_date(book_with_full_metadata: BookWithFullRelations) -> None:
    """Test _add_modified_date (covers lines 353-368)."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_with_full_metadata)
    service._add_modified_date(metadata, structured)

    modified_meta = metadata.findall('.//meta[@property="dcterms:modified"]')
    assert len(modified_meta) == 1
    assert modified_meta[0].text is not None
    # Should be in ISO format
    assert "T" in modified_meta[0].text or modified_meta[0].text.endswith("Z")


def test_add_modified_date_with_plus_00_00(book: Book) -> None:
    """Test _add_modified_date with +00:00 timezone."""
    book_with_timestamp = BookWithFullRelations(
        book=book,
        authors=[],
        series=None,
        series_id=None,
        tags=[],
        identifiers=[],
        description=None,
        publisher=None,
        publisher_id=None,
        languages=[],
        language_ids=[],
        rating=None,
        rating_id=None,
        formats=[],
    )

    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_with_timestamp)
    # Mock timestamp with +00:00
    structured.timestamp = "2020-01-01T12:00:00+00:00"
    service._add_modified_date(metadata, structured)

    modified_meta = metadata.findall('.//meta[@property="dcterms:modified"]')
    assert len(modified_meta) == 1
    # Should convert +00:00 to Z
    assert modified_meta[0].text.endswith("Z")


def test_add_modified_date_without_z(book: Book) -> None:
    """Test _add_modified_date without Z suffix."""
    book_with_timestamp = BookWithFullRelations(
        book=book,
        authors=[],
        series=None,
        series_id=None,
        tags=[],
        identifiers=[],
        description=None,
        publisher=None,
        publisher_id=None,
        languages=[],
        language_ids=[],
        rating=None,
        rating_id=None,
        formats=[],
    )

    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_with_timestamp)
    # Mock timestamp without Z
    structured.timestamp = "2020-01-01T12:00:00"
    service._add_modified_date(metadata, structured)

    modified_meta = metadata.findall('.//meta[@property="dcterms:modified"]')
    assert len(modified_meta) == 1
    # Should add Z suffix
    assert modified_meta[0].text.endswith("Z")


def test_add_modified_date_without_timestamp(
    book_minimal: BookWithFullRelations,
) -> None:
    """Test _add_modified_date without timestamp."""
    service = OpfService()
    package = service._create_package_element()
    metadata = etree.SubElement(package, "metadata")

    from bookcard.services.metadata_builder import MetadataBuilder

    structured = MetadataBuilder.build(book_minimal)
    structured.timestamp = None
    service._add_modified_date(metadata, structured)

    modified_meta = metadata.findall('.//meta[@property="dcterms:modified"]')
    assert len(modified_meta) == 0
