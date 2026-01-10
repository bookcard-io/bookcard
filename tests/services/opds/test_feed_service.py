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

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest
from fastapi import Request
from sqlmodel import Session

from bookcard.api.schemas.opds import OpdsFeedRequest, OpdsFeedResponse
from bookcard.models.config import Library
from bookcard.models.core import Author
from bookcard.repositories.models import BookWithRelations
from bookcard.services.opds.book_query_service import OpdsBookQueryService
from bookcard.services.opds.feed_service import OpdsFeedService
from bookcard.services.opds.xml_builder import OpdsXmlBuilder


@pytest.fixture
def mock_session() -> Mock:
    return Mock(spec=Session)


@pytest.fixture
def mock_library() -> Mock:
    lib = Mock(spec=Library)
    lib.name = "Test Library"
    return lib


@pytest.fixture
def mock_xml_builder() -> Mock:
    return Mock(spec=OpdsXmlBuilder)


@pytest.fixture
def mock_book_query_service() -> Mock:
    return Mock(spec=OpdsBookQueryService)


@pytest.fixture
def mock_request() -> Mock:
    request = Mock(spec=Request)
    request.base_url = "http://testserver/"
    return request


@pytest.fixture
def feed_service(
    mock_session: Mock,
    mock_library: Mock,
    mock_xml_builder: Mock,
    mock_book_query_service: Mock,
) -> OpdsFeedService:
    with patch("bookcard.services.opds.feed_service.BookService"):
        return OpdsFeedService(
            session=mock_session,
            library=mock_library,
            xml_builder=mock_xml_builder,
            book_query_service=mock_book_query_service,
        )


@pytest.fixture
def feed_request() -> OpdsFeedRequest:
    return OpdsFeedRequest(offset=0, page_size=20)


@pytest.fixture
def mock_book() -> Mock:
    book_rel = Mock(spec=BookWithRelations)
    book_rel.book = Mock()
    book_rel.book.id = 1
    book_rel.book.title = "Test Book"
    book_rel.book.uuid = "00000000-0000-0000-0000-000000000001"
    book_rel.book.has_cover = True
    book_rel.book.pubdate = datetime(2023, 1, 1, tzinfo=UTC)
    book_rel.book.last_modified = datetime(2023, 1, 2, tzinfo=UTC)
    book_rel.book.isbn = "123"
    book_rel.book.series_index = 1.0
    book_rel.authors = ["Author"]
    book_rel.series = "Series"
    book_rel.formats = [{"format": "EPUB", "name": "1.epub", "size": 1000}]
    book_rel.is_virtual = False
    return book_rel


class TestOpdsFeedService:
    def test_init_defaults(self, mock_session: Mock, mock_library: Mock) -> None:
        """Test initialization with defaults."""
        with (
            patch("bookcard.services.opds.feed_service.BookService"),
            patch("bookcard.services.opds.feed_service.OpdsXmlBuilder"),
            patch("bookcard.services.opds.feed_service.OpdsBookQueryService"),
        ):
            service = OpdsFeedService(mock_session, mock_library)
            assert service._xml_builder is not None
            assert service._book_query_service is not None

    def test_generate_catalog_feed(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_xml_builder: Mock,
        mock_book_query_service: Mock,
    ) -> None:
        """Test generating catalog feed."""
        mock_xml_builder.build_feed.return_value = "<feed></feed>"
        mock_book_query_service.get_recent_books.return_value = ([], 0)

        response = feed_service.generate_catalog_feed(mock_request, None)

        assert isinstance(response, OpdsFeedResponse)
        assert response.xml_content == "<feed></feed>"
        mock_xml_builder.build_feed.assert_called()
        call_args = mock_xml_builder.build_feed.call_args[1]
        assert call_args["title"] == "Calibre Library - Test Library"
        assert len(call_args["links"]) == 4  # 4 main links

    def test_generate_books_feed(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_book_query_service: Mock,
        mock_xml_builder: Mock,
        feed_request: OpdsFeedRequest,
        mock_book: Mock,
    ) -> None:
        """Test generating books feed."""
        mock_book_query_service.get_books.return_value = ([mock_book], 1)
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        response = feed_service.generate_books_feed(mock_request, None, feed_request)

        assert isinstance(response, OpdsFeedResponse)
        mock_book_query_service.get_books.assert_called_with(
            user=None, page=1, page_size=20
        )
        mock_xml_builder.build_feed.assert_called()
        entries = mock_xml_builder.build_feed.call_args[1]["entries"]
        assert len(entries) == 1
        assert entries[0].id == "urn:uuid:00000000-0000-0000-0000-000000000001"

    def test_generate_new_feed(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_book_query_service: Mock,
        mock_xml_builder: Mock,
        feed_request: OpdsFeedRequest,
        mock_book: Mock,
    ) -> None:
        """Test generating new books feed."""
        mock_book_query_service.get_recent_books.return_value = ([mock_book], 1)
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        feed_service.generate_new_feed(mock_request, None, feed_request)

        mock_book_query_service.get_recent_books.assert_called_with(
            user=None, page=1, page_size=20
        )

    def test_generate_discover_feed(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_book_query_service: Mock,
        mock_xml_builder: Mock,
        feed_request: OpdsFeedRequest,
        mock_book: Mock,
    ) -> None:
        """Test generating discover feed."""
        mock_book_query_service.get_random_books.return_value = [mock_book]
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        feed_service.generate_discover_feed(mock_request, None, feed_request)

        mock_book_query_service.get_random_books.assert_called_with(user=None, limit=20)

    def test_generate_search_feed(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_book_query_service: Mock,
        mock_xml_builder: Mock,
        feed_request: OpdsFeedRequest,
        mock_book: Mock,
    ) -> None:
        """Test generating search feed."""
        mock_book_query_service.search_books.return_value = ([mock_book], 1)
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        feed_service.generate_search_feed(mock_request, None, "query", feed_request)

        mock_book_query_service.search_books.assert_called_with(
            user=None, query="query", page=1, page_size=20
        )

    def test_generate_opensearch_description(
        self, feed_service: OpdsFeedService, mock_request: Mock
    ) -> None:
        """Test generating opensearch description."""
        response = feed_service.generate_opensearch_description(mock_request)

        assert response.content_type == "application/opensearchdescription+xml"
        assert "<OpenSearchDescription" in response.xml_content

    def test_generate_books_by_letter_feed(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_book_query_service: Mock,
        mock_xml_builder: Mock,
        feed_request: OpdsFeedRequest,
        mock_book: Mock,
    ) -> None:
        """Test generating books by letter feed."""
        mock_book.book.title_sort = "Test"
        mock_book_query_service.get_books.return_value = ([mock_book], 1)
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        feed_service.generate_books_by_letter_feed(
            mock_request, None, "T", feed_request
        )

        # Should call get_books with title_sort
        mock_book_query_service.get_books.assert_called()
        call_args = mock_book_query_service.get_books.call_args[1]
        assert call_args["sort_by"] == "title_sort"

        # Verify filtering logic (though it happens in the method, we check result implicitly via entries if we inspected them)

    def test_generate_books_by_letter_feed_filter(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_book_query_service: Mock,
        mock_xml_builder: Mock,
        feed_request: OpdsFeedRequest,
    ) -> None:
        """Test filtering in books by letter feed."""
        # Book starts with T
        book1 = Mock(spec=BookWithRelations)
        book1.book = Mock()
        book1.book.id = 1
        book1.book.title = "Test Book"
        book1.book.title_sort = "Test"
        book1.book.has_cover = False
        book1.book.pubdate = None
        book1.book.last_modified = datetime(2023, 1, 1, tzinfo=UTC)
        book1.book.isbn = None
        book1.book.uuid = "00000000-0000-0000-0000-000000000001"
        book1.book.series_index = 1.0
        book1.authors = ["Author"]
        book1.series = None
        book1.formats = [{"format": "EPUB", "name": "1.epub", "size": 1000}]
        book1.is_virtual = False

        # Book starts with A
        book2 = Mock(spec=BookWithRelations)
        book2.book = Mock()
        book2.book.id = 2
        book2.book.title = "Apple Book"
        book2.book.title_sort = "Apple"
        book2.book.has_cover = False
        book2.book.pubdate = None
        book2.book.last_modified = datetime(2023, 1, 1, tzinfo=UTC)
        book2.book.isbn = None
        book2.book.uuid = "00000000-0000-0000-0000-000000000002"
        book2.book.series_index = 1.0
        book2.authors = ["Author"]
        book2.series = None
        book2.formats = [{"format": "EPUB", "name": "2.epub", "size": 1000}]
        book2.is_virtual = False

        mock_book_query_service.get_books.return_value = ([book1, book2], 2)
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        feed_service.generate_books_by_letter_feed(
            mock_request, None, "T", feed_request
        )

        # Only book1 should be in entries
        entries = mock_xml_builder.build_feed.call_args[1]["entries"]
        assert len(entries) == 1
        # UUID is used when available
        assert entries[0].id.startswith("urn:uuid:")

    def test_generate_rated_feed(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_book_query_service: Mock,
        mock_xml_builder: Mock,
        feed_request: OpdsFeedRequest,
    ) -> None:
        """Test generating rated feed."""
        mock_book_query_service.get_best_rated_books.return_value = ([], 0)
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        feed_service.generate_rated_feed(mock_request, None, feed_request)

        mock_book_query_service.get_best_rated_books.assert_called()

    def test_generate_author_index_feed(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_session: Mock,
        mock_xml_builder: Mock,
        feed_request: OpdsFeedRequest,
    ) -> None:
        """Test generating author index feed."""
        # Mock session exec for authors
        author = Author(id=1, name="Author", sort="Author")
        mock_exec = Mock()
        mock_exec.all.return_value = [author]
        mock_session.exec.return_value = mock_exec
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        feed_service.generate_author_index_feed(mock_request, feed_request)

        mock_session.exec.assert_called()
        entries = mock_xml_builder.build_feed.call_args[1]["entries"]
        assert len(entries) == 1
        assert entries[0].title == "Author"

    def test_generate_author_letter_feed(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_session: Mock,
        mock_xml_builder: Mock,
        feed_request: OpdsFeedRequest,
    ) -> None:
        """Test generating author letter feed."""
        author = Author(id=1, name="Author", sort="Author")
        mock_exec = Mock()
        mock_exec.all.return_value = [author]
        mock_session.exec.return_value = mock_exec
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        feed_service.generate_author_letter_feed(mock_request, "A", feed_request)

        mock_session.exec.assert_called()

    def test_generate_books_by_author_feed(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_book_query_service: Mock,
        mock_xml_builder: Mock,
        feed_request: OpdsFeedRequest,
    ) -> None:
        """Test generating books by author feed."""
        mock_book_query_service.get_books_by_filter.return_value = ([], 0)
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        feed_service.generate_books_by_author_feed(mock_request, None, 1, feed_request)

        mock_book_query_service.get_books_by_filter.assert_called()
        call_args = mock_book_query_service.get_books_by_filter.call_args[1]
        assert call_args["author_ids"] == [1]

    # Test generic methods using parametrize
    @pytest.mark.parametrize(
        ("method_name", "path", "title"),
        [
            ("generate_publisher_index_feed", "publisher", "Publishers"),
            ("generate_category_index_feed", "category", "Categories"),
            ("generate_series_index_feed", "series", "Series"),
            ("generate_rating_index_feed", "ratings", "Ratings"),
            ("generate_format_index_feed", "formats", "Formats"),
            ("generate_language_index_feed", "language", "Languages"),
            ("generate_shelf_index_feed", "shelfindex", "Shelves"),
        ],
    )
    def test_generic_index_feeds(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_xml_builder: Mock,
        method_name: str,
        path: str,
        title: str,
    ) -> None:
        """Test generic index feed generation."""
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        method = getattr(feed_service, method_name)
        method(mock_request)

        mock_xml_builder.build_feed.assert_called()
        call_args = mock_xml_builder.build_feed.call_args[1]
        assert call_args["title"] == title
        assert f"/opds/{path}" in call_args["feed_id"]

    @pytest.mark.parametrize(
        ("method_name", "filter_arg", "filter_val", "query_arg"),
        [
            ("generate_books_by_publisher_feed", "publisher_id", 1, "publisher_ids"),
            ("generate_books_by_category_feed", "category_id", 1, "genre_ids"),
            ("generate_books_by_series_feed", "series_id", 1, "series_ids"),
            ("generate_books_by_rating_feed", "rating_id", 1, "rating_ids"),
            ("generate_books_by_language_feed", "language_id", 1, "language_ids"),
        ],
    )
    def test_generic_books_by_filter_feeds(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_book_query_service: Mock,
        mock_xml_builder: Mock,
        feed_request: OpdsFeedRequest,
        method_name: str,
        filter_arg: str,
        filter_val: int,
        query_arg: str,
    ) -> None:
        """Test generic books by filter feed generation."""
        mock_book_query_service.get_books_by_filter.return_value = ([], 0)
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        method = getattr(feed_service, method_name)
        kwargs = {
            "request": mock_request,
            "user": None,
            "feed_request": feed_request,
            filter_arg: filter_val,
        }
        method(**kwargs)

        mock_book_query_service.get_books_by_filter.assert_called()
        call_args = mock_book_query_service.get_books_by_filter.call_args[1]
        assert call_args[query_arg] == [filter_val]

    def test_generate_books_by_format_feed(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_book_query_service: Mock,
        mock_xml_builder: Mock,
        feed_request: OpdsFeedRequest,
    ) -> None:
        """Test generating books by format feed."""
        mock_book_query_service.get_books_by_filter.return_value = ([], 0)
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        feed_service.generate_books_by_format_feed(
            mock_request, None, "EPUB", feed_request
        )

        mock_book_query_service.get_books_by_filter.assert_called()
        call_args = mock_book_query_service.get_books_by_filter.call_args[1]
        assert call_args["formats"] == ["EPUB"]

    def test_generate_hot_feed(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_book_query_service: Mock,
        mock_xml_builder: Mock,
        feed_request: OpdsFeedRequest,
    ) -> None:
        """Test hot feed (currently delegates to new)."""
        mock_book_query_service.get_recent_books.return_value = ([], 0)
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        feed_service.generate_hot_feed(mock_request, None, feed_request)

        mock_book_query_service.get_recent_books.assert_called()

    @pytest.mark.parametrize(
        ("method_name", "title"),
        [
            ("generate_read_books_feed", "Read Books"),
            ("generate_unread_books_feed", "Unread Books"),
        ],
    )
    def test_read_status_feeds(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_xml_builder: Mock,
        method_name: str,
        title: str,
    ) -> None:
        """Test read/unread books feeds (currently placeholders)."""
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        method = getattr(feed_service, method_name)
        method(mock_request)

        mock_xml_builder.build_feed.assert_called()
        assert mock_xml_builder.build_feed.call_args[1]["title"] == title

    def test_pagination_links(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_book_query_service: Mock,
        mock_xml_builder: Mock,
    ) -> None:
        """Test pagination link generation logic in build_books_feed."""
        # Request for page 2 of 4
        feed_request = OpdsFeedRequest(offset=20, page_size=20)
        mock_book_query_service.get_books.return_value = ([], 80)  # 80 total = 4 pages
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        feed_service.generate_books_feed(mock_request, None, feed_request)

        links = mock_xml_builder.build_feed.call_args[1]["links"]
        # _build_books_feed generates: self + full pagination set
        rels = [link["rel"] for link in links]
        assert "self" in rels
        assert "first" in rels
        assert "previous" in rels
        assert "next" in rels
        assert "last" in rels

    def test_build_entries_skips_no_id(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_xml_builder: Mock,
        mock_book: Mock,
    ) -> None:
        """Test build_entries skips books with no ID."""
        mock_book.book.id = None

        # Access private method for testing logic
        entries = feed_service._build_entries(mock_request, [mock_book])

        assert len(entries) == 0

    def test_search_feed_with_pagination_and_query(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_book_query_service: Mock,
        mock_xml_builder: Mock,
        feed_request: OpdsFeedRequest,
        mock_book: Mock,
    ) -> None:
        """Test search feed with pagination includes query in links."""
        # Page 2 with query
        feed_request = OpdsFeedRequest(offset=20, page_size=20)
        mock_book_query_service.search_books.return_value = ([mock_book], 80)
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        feed_service.generate_search_feed(
            mock_request, None, "test query", feed_request
        )

        # Check that query is included in pagination links
        links = mock_xml_builder.build_feed.call_args[1]["links"]
        rels = [link["rel"] for link in links]
        assert "self" in rels
        # Verify query param is in URLs
        for link_item in links:
            if link_item["rel"] in ["self", "first", "previous", "next", "last"]:
                assert (
                    "query=test+query" in link_item["href"]
                    or "query=test%20query" in link_item["href"]
                )

    def test_build_pagination_links_edge_cases(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_book_query_service: Mock,
        mock_xml_builder: Mock,
    ) -> None:
        """Test _build_pagination_links with various offset scenarios."""
        from bookcard.services.opds.url_builder import OpdsUrlBuilder

        url_builder = OpdsUrlBuilder(mock_request)

        # Test: offset = 0 (clamped prev to first; full link set)
        links = feed_service._build_pagination_links(
            url_builder, "/opds/test", 0, 20, 100
        )
        rels = [link["rel"] for link in links]
        assert "first" in rels
        assert "previous" in rels
        assert "next" in rels
        assert "last" in rels
        href_by_rel = {link["rel"]: link["href"] for link in links}
        assert "offset=0" in href_by_rel["previous"]

        # Test: offset at end (clamped next to last; full link set)
        links = feed_service._build_pagination_links(
            url_builder, "/opds/test", 80, 20, 100
        )
        rels = [link["rel"] for link in links]
        assert "first" in rels
        assert "previous" in rels
        assert "next" in rels
        assert "last" in rels
        href_by_rel = {link["rel"]: link["href"] for link in links}
        assert "offset=80" in href_by_rel["next"]

        # Test offset in middle
        links = feed_service._build_pagination_links(
            url_builder, "/opds/test", 40, 20, 100
        )
        rels = [link["rel"] for link in links]
        assert "first" in rels
        assert "previous" in rels
        assert "next" in rels
        assert "last" in rels

        # Test total <= page_size (no pagination)
        links = feed_service._build_pagination_links(
            url_builder, "/opds/test", 0, 20, 20
        )
        assert links == []

    def test_generate_author_letter_feed_all(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_session: Mock,
        mock_xml_builder: Mock,
        feed_request: OpdsFeedRequest,
    ) -> None:
        """Test author letter feed with '00' (all authors)."""
        author = Author(id=1, name="Author", sort="Author")
        mock_exec = Mock()
        mock_exec.all.return_value = [author]
        mock_session.exec.return_value = mock_exec
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        feed_service.generate_author_letter_feed(mock_request, "00", feed_request)

        mock_session.exec.assert_called()

    def test_build_author_entries_skips_no_id(
        self,
        feed_service: OpdsFeedService,
        mock_request: Mock,
        mock_xml_builder: Mock,
    ) -> None:
        """Test _build_author_entries skips authors with no ID."""
        author1 = Author(id=1, name="Author 1")
        author2 = Author(id=None, name="Author 2")

        entries = feed_service._build_author_entries(mock_request, [author1, author2])

        assert len(entries) == 1
        assert entries[0].title == "Author 1"

    def test_generate_category_letter_feed(
        self, feed_service: OpdsFeedService, mock_request: Mock, mock_xml_builder: Mock
    ) -> None:
        """Test category letter feed."""
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        feed_service.generate_category_letter_feed(mock_request, "A")

        mock_xml_builder.build_feed.assert_called()
        call_args = mock_xml_builder.build_feed.call_args[1]
        assert "Categories" in call_args["title"]

    def test_generate_series_letter_feed(
        self, feed_service: OpdsFeedService, mock_request: Mock, mock_xml_builder: Mock
    ) -> None:
        """Test series letter feed."""
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        feed_service.generate_series_letter_feed(mock_request, "A")

        mock_xml_builder.build_feed.assert_called()
        call_args = mock_xml_builder.build_feed.call_args[1]
        assert "Series" in call_args["title"]

    def test_generate_books_by_shelf_feed(
        self, feed_service: OpdsFeedService, mock_request: Mock, mock_xml_builder: Mock
    ) -> None:
        """Test books by shelf feed (placeholder implementation)."""
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        response = feed_service.generate_books_by_shelf_feed(mock_request, 1)

        assert isinstance(response, OpdsFeedResponse)
        mock_xml_builder.build_feed.assert_called()
        call_args = mock_xml_builder.build_feed.call_args[1]
        assert "Shelf 1" in call_args["title"]
        assert len(call_args["entries"]) == 0  # Placeholder returns empty

    def test_generate_generic_letter_feed(
        self, feed_service: OpdsFeedService, mock_request: Mock, mock_xml_builder: Mock
    ) -> None:
        """Test _generate_generic_letter_feed helper."""
        mock_xml_builder.build_feed.return_value = "<feed></feed>"

        # Access private method
        response = feed_service._generate_generic_letter_feed(
            mock_request, "A", "test", "Test Title"
        )

        assert isinstance(response, OpdsFeedResponse)
        mock_xml_builder.build_feed.assert_called()
        call_args = mock_xml_builder.build_feed.call_args[1]
        assert "Test Title - A" in call_args["title"]

        # Test with "00" (all)
        response = feed_service._generate_generic_letter_feed(
            mock_request, "00", "test", "Test Title"
        )
        call_args = mock_xml_builder.build_feed.call_args[1]
        assert "Test Title - All" in call_args["title"]
