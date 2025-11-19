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

"""Tests for OpenLibrary data source to achieve 100% coverage."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import httpx
import pytest

from fundamental.services.library_scanning.data_sources.base import (
    DataSourceNetworkError,
    DataSourceNotFoundError,
    DataSourceRateLimitError,
)
from fundamental.services.library_scanning.data_sources.openlibrary import (
    OPENLIBRARY_API_BASE,
    OPENLIBRARY_COVERS_BASE,
    OPENLIBRARY_MAX_PAGE_SIZE,
    AuthorWorksPaginator,
    OpenLibraryDataSource,
    PaginationState,
    PaginationStrategy,
    SearchRequestBuilder,
    WorkKeyExtractor,
)
from fundamental.services.library_scanning.data_sources.types import (
    IdentifierDict,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_httpx_client() -> MagicMock:
    """Create a mock httpx client."""
    client = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {}
    response.raise_for_status.return_value = None
    client.get.return_value = response
    client.__enter__.return_value = client
    client.__exit__.return_value = None
    return client


@pytest.fixture
def data_source() -> OpenLibraryDataSource:
    """Create OpenLibraryDataSource instance."""
    return OpenLibraryDataSource(
        base_url="https://test.openlibrary.org",
        timeout=10.0,
        rate_limit_delay=0.1,
    )


@pytest.fixture
def pagination_state() -> PaginationState:
    """Create PaginationState instance."""
    return PaginationState()


@pytest.fixture
def pagination_strategy() -> PaginationStrategy:
    """Create PaginationStrategy instance."""
    return PaginationStrategy()


@pytest.fixture
def work_extractor() -> WorkKeyExtractor:
    """Create WorkKeyExtractor instance."""
    return WorkKeyExtractor()


@pytest.fixture
def request_builder() -> SearchRequestBuilder:
    """Create SearchRequestBuilder instance."""
    return SearchRequestBuilder(author_key="OL123A", lang="eng", fields="key")


@pytest.fixture
def sample_author_data() -> dict[str, object]:
    """Create sample author data from API."""
    return {
        "key": "/authors/OL123A",
        "name": "Test Author",
        "personal_name": "Author",
        "fuller_name": "Test Author",
        "title": "Dr.",
        "birth_date": "1950-01-01",
        "death_date": "2020-01-01",
        "entity_type": {"key": "/type/author"},
        "work_count": 10,
        "ratings_average": 4.5,
        "ratings_count": 100,
        "top_work": "Test Book",
        "photos": [12345, 67890],
        "top_subjects": ["Fiction", "Science Fiction"],
        "bio": {"value": "Test biography"},
        "alternate_names": ["Alt Name 1", "Alt Name 2"],
        "links": [
            {"title": "Website", "url": "https://example.com", "type": {"key": "web"}}
        ],
        "remote_ids": {
            "viaf": "123456",
            "goodreads": "789012",
            "wikidata": "Q123",
        },
    }


@pytest.fixture
def sample_book_data() -> dict[str, object]:
    """Create sample book data from API."""
    return {
        "key": "/works/OL123W",
        "title": "Test Book",
        "authors": [
            {"author": {"key": "/authors/OL123A"}},
            {"author": {"key": "/authors/OL456A"}},
        ],
        "identifiers": {
            "isbn_10": ["1234567890"],
            "isbn_13": ["9781234567890"],
        },
        "covers": [12345],
        "first_publish_date": "2020-01-01",
        "publishers": [{"name": "Test Publisher"}],
        "subjects": [
            "Fiction",
            {"name": "Science Fiction"},
            {"key": "/subjects/sci-fi"},
        ],
        "description": {"value": "Test description"},
    }


@pytest.fixture
def sample_search_doc() -> dict[str, object]:
    """Create sample search document."""
    return {
        "key": "/works/OL123W",
        "title": "Test Book",
        "author_name": ["Test Author"],
        "isbn": ["1234567890", "9781234567890"],
        "cover_i": 12345,
        "first_publish_year": 2020,
        "publisher": ["Test Publisher"],
        "subject": ["Fiction", "Science Fiction"],
    }


# ============================================================================
# PaginationState Tests
# ============================================================================


class TestPaginationState:
    """Test PaginationState."""

    def test_init_defaults(self) -> None:
        """Test __init__ with default values."""
        state = PaginationState()

        assert state.offset == 0
        assert state.collected_count == 0
        assert state.page_size == OPENLIBRARY_MAX_PAGE_SIZE

    def test_init_custom(self) -> None:
        """Test __init__ with custom values."""
        state = PaginationState(offset=10, collected_count=5, page_size=50)

        assert state.offset == 10
        assert state.collected_count == 5
        assert state.page_size == 50


# ============================================================================
# PaginationStrategy Tests
# ============================================================================


class TestPaginationStrategy:
    """Test PaginationStrategy."""

    def test_init_no_limit(self) -> None:
        """Test __init__ with no limit."""
        strategy = PaginationStrategy()

        assert strategy.total_limit is None

    def test_init_with_limit(self) -> None:
        """Test __init__ with limit."""
        strategy = PaginationStrategy(total_limit=100)

        assert strategy.total_limit == 100

    @pytest.mark.parametrize(
        ("total_limit", "collected_count", "page_size", "expected"),
        [
            (None, 0, 100, 100),
            (100, 0, 100, 100),
            (100, 50, 100, 50),
            (100, 90, 100, 10),
            (100, 100, 100, 0),
            (100, 150, 100, 0),
        ],
    )
    def test_calculate_request_limit(
        self,
        total_limit: int | None,
        collected_count: int,
        page_size: int,
        expected: int,
        pagination_state: PaginationState,
    ) -> None:
        """Test calculate_request_limit."""
        strategy = PaginationStrategy(total_limit=total_limit)
        pagination_state.collected_count = collected_count

        result = strategy.calculate_request_limit(pagination_state, page_size)

        assert result == expected

    @pytest.mark.parametrize(
        ("docs_count", "total_found", "collected_count", "total_limit", "expected"),
        [
            (0, 100, 0, None, False),  # No docs
            (10, 100, 0, None, True),  # Has docs, not at end
            (10, 100, 0, 50, True),  # Has docs, under limit
            (10, 100, 50, 50, False),  # Reached limit
            (10, 100, 45, 50, True),  # Under limit
            (10, 100, 100, None, False),  # Reached end
            (10, 100, 90, None, False),  # At end (90 + 10 = 100, not < 100)
        ],
    )
    def test_should_continue(
        self,
        docs_count: int,
        total_found: int,
        collected_count: int,
        total_limit: int | None,
        expected: bool,
        pagination_state: PaginationState,
    ) -> None:
        """Test should_continue."""
        strategy = PaginationStrategy(total_limit=total_limit)
        pagination_state.collected_count = collected_count
        pagination_state.offset = collected_count

        result = strategy.should_continue(pagination_state, docs_count, total_found)

        assert result == expected

    def test_update_state(
        self, pagination_state: PaginationState, pagination_strategy: PaginationStrategy
    ) -> None:
        """Test update_state."""
        initial_count = pagination_state.collected_count
        initial_offset = pagination_state.offset
        docs_count = 10

        pagination_strategy.update_state(pagination_state, docs_count)

        assert pagination_state.collected_count == initial_count + docs_count
        assert pagination_state.offset == initial_offset + docs_count


# ============================================================================
# WorkKeyExtractor Tests
# ============================================================================


class TestWorkKeyExtractor:
    """Test WorkKeyExtractor."""

    @pytest.mark.parametrize(
        ("docs", "expected"),
        [
            ([], []),
            ([{"key": "/works/OL123W"}], ["OL123W"]),
            ([{"key": "/books/OL123M"}], ["OL123M"]),
            (
                [{"key": "/works/OL123W"}, {"key": "/books/OL456M"}],
                ["OL123W", "OL456M"],
            ),
            ([{"key": ""}], []),
            ([{"key": "/works/"}], []),
            ([{"key": "/books/"}], []),
            ([{"other": "value"}], []),
        ],
    )
    def test_extract(
        self,
        docs: list[dict[str, object]],
        expected: list[str],
        work_extractor: WorkKeyExtractor,
    ) -> None:
        """Test extract."""
        result = work_extractor.extract(docs)

        assert result == expected


# ============================================================================
# SearchRequestBuilder Tests
# ============================================================================


class TestSearchRequestBuilder:
    """Test SearchRequestBuilder."""

    def test_init_defaults(self) -> None:
        """Test __init__ with defaults."""
        builder = SearchRequestBuilder(author_key="OL123A")

        assert builder.author_key == "OL123A"
        assert builder.lang == "eng"
        assert builder.fields == "key"

    def test_init_custom(self) -> None:
        """Test __init__ with custom values."""
        builder = SearchRequestBuilder(
            author_key="OL123A", lang="fra", fields="key,title"
        )

        assert builder.author_key == "OL123A"
        assert builder.lang == "fra"
        assert builder.fields == "key,title"

    @pytest.mark.parametrize(
        ("limit", "offset", "expected"),
        [
            (
                10,
                0,
                {
                    "author": "OL123A",
                    "lang": "eng",
                    "fields": "key",
                    "limit": 10,
                    "offset": 0,
                },
            ),
            (
                50,
                100,
                {
                    "author": "OL123A",
                    "lang": "eng",
                    "fields": "key",
                    "limit": 50,
                    "offset": 100,
                },
            ),
        ],
    )
    def test_build_params(
        self,
        limit: int,
        offset: int,
        expected: dict[str, object],
        request_builder: SearchRequestBuilder,
    ) -> None:
        """Test build_params."""
        result = request_builder.build_params(limit, offset)

        assert result == expected


# ============================================================================
# AuthorWorksPaginator Tests
# ============================================================================


class TestAuthorWorksPaginator:
    """Test AuthorWorksPaginator."""

    @pytest.fixture
    def make_request(self) -> MagicMock:
        """Create mock make_request function."""
        return MagicMock(return_value={"docs": [], "numFound": 0})

    @pytest.fixture
    def rate_limit(self) -> MagicMock:
        """Create mock rate_limit function."""
        return MagicMock()

    @pytest.fixture
    def paginator(
        self,
        request_builder: SearchRequestBuilder,
        pagination_strategy: PaginationStrategy,
        work_extractor: WorkKeyExtractor,
        make_request: MagicMock,
        rate_limit: MagicMock,
    ) -> AuthorWorksPaginator:
        """Create AuthorWorksPaginator instance."""
        return AuthorWorksPaginator(
            request_builder=request_builder,
            pagination_strategy=pagination_strategy,
            work_extractor=work_extractor,
            make_request=make_request,
            rate_limit=rate_limit,
        )

    def test_fetch_all_empty(
        self, paginator: AuthorWorksPaginator, make_request: MagicMock
    ) -> None:
        """Test fetch_all with empty results."""
        result = paginator.fetch_all()

        assert result == []
        make_request.assert_called_once()

    def test_fetch_all_single_page(
        self, paginator: AuthorWorksPaginator, make_request: MagicMock
    ) -> None:
        """Test fetch_all with single page."""
        make_request.return_value = {
            "docs": [{"key": "/works/OL123W"}, {"key": "/books/OL456M"}],
            "numFound": 2,
        }

        result = paginator.fetch_all()

        assert result == ["OL123W", "OL456M"]
        make_request.assert_called_once()

    def test_fetch_all_multiple_pages(
        self,
        paginator: AuthorWorksPaginator,
        make_request: MagicMock,
        rate_limit: MagicMock,
    ) -> None:
        """Test fetch_all with multiple pages."""
        make_request.side_effect = [
            {
                "docs": [{"key": "/works/OL1W"} for _ in range(100)],
                "numFound": 250,
            },
            {
                "docs": [{"key": "/works/OL2W"} for _ in range(100)],
                "numFound": 250,
            },
            {
                "docs": [{"key": "/works/OL3W"} for _ in range(50)],
                "numFound": 250,
            },
        ]

        result = paginator.fetch_all()

        assert len(result) == 250
        assert make_request.call_count == 3
        assert rate_limit.call_count == 2  # Called between pages

    def test_fetch_all_with_limit(
        self, make_request: MagicMock, rate_limit: MagicMock
    ) -> None:
        """Test fetch_all with limit."""
        strategy = PaginationStrategy(total_limit=50)
        paginator = AuthorWorksPaginator(
            request_builder=SearchRequestBuilder("OL123A"),
            pagination_strategy=strategy,
            work_extractor=WorkKeyExtractor(),
            make_request=make_request,
            rate_limit=rate_limit,
        )
        make_request.return_value = {
            "docs": [{"key": "/works/OL1W"} for _ in range(100)],
            "numFound": 1000,
        }

        result = paginator.fetch_all()

        assert len(result) == 50
        make_request.assert_called_once()

    def test_fetch_all_stops_at_zero_limit(
        self, paginator: AuthorWorksPaginator, make_request: MagicMock
    ) -> None:
        """Test fetch_all stops when limit is zero."""
        strategy = PaginationStrategy(total_limit=0)
        paginator = AuthorWorksPaginator(
            request_builder=SearchRequestBuilder("OL123A"),
            pagination_strategy=strategy,
            work_extractor=WorkKeyExtractor(),
            make_request=make_request,
            rate_limit=MagicMock(),
        )

        result = paginator.fetch_all()

        assert result == []
        make_request.assert_not_called()

    def test_fetch_all_extracts_remaining_on_break(
        self, paginator: AuthorWorksPaginator, make_request: MagicMock
    ) -> None:
        """Test fetch_all extracts remaining keys before breaking."""
        make_request.return_value = {
            "docs": [{"key": "/works/OL1W"}, {"key": "/works/OL2W"}],
            "numFound": 2,
        }

        result = paginator.fetch_all()

        assert result == ["OL1W", "OL2W"]


# ============================================================================
# OpenLibraryDataSource Tests
# ============================================================================


class TestOpenLibraryDataSourceInit:
    """Test OpenLibraryDataSource initialization."""

    def test_init_defaults(self) -> None:
        """Test __init__ with defaults."""
        source = OpenLibraryDataSource()

        assert source.base_url == OPENLIBRARY_API_BASE
        assert source.timeout == 30.0
        assert source.rate_limit_delay == 0.5
        assert source._last_request_time == 0.0

    def test_init_custom(self) -> None:
        """Test __init__ with custom values."""
        source = OpenLibraryDataSource(
            base_url="https://custom.org", timeout=60.0, rate_limit_delay=1.0
        )

        assert source.base_url == "https://custom.org"
        assert source.timeout == 60.0
        assert source.rate_limit_delay == 1.0

    def test_init_strips_trailing_slash(self) -> None:
        """Test __init__ strips trailing slash from base_url."""
        source = OpenLibraryDataSource(base_url="https://test.org/")

        assert source.base_url == "https://test.org"

    def test_name_property(self, data_source: OpenLibraryDataSource) -> None:
        """Test name property."""
        assert data_source.name == "OpenLibrary"


class TestOpenLibraryDataSourceRateLimit:
    """Test OpenLibraryDataSource rate limiting."""

    def test_rate_limit_no_delay(
        self, data_source: OpenLibraryDataSource, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test _rate_limit when no delay needed."""
        mock_sleep = MagicMock()
        monkeypatch.setattr("time.sleep", mock_sleep)
        data_source._last_request_time = time.time() - 1.0

        data_source._rate_limit()

        mock_sleep.assert_not_called()

    def test_rate_limit_with_delay(
        self, data_source: OpenLibraryDataSource, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test _rate_limit when delay is needed."""
        mock_sleep = MagicMock()
        monkeypatch.setattr("time.sleep", mock_sleep)
        data_source._last_request_time = time.time()

        data_source._rate_limit()

        mock_sleep.assert_called_once()
        assert mock_sleep.call_args[0][0] > 0


class TestOpenLibraryDataSourceMakeRequest:
    """Test OpenLibraryDataSource _make_request."""

    def test_make_request_success(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test _make_request with successful response."""
        mock_httpx_client.get.return_value.json.return_value = {"key": "value"}

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source._make_request("/test.json")

        assert result == {"key": "value"}
        mock_httpx_client.get.assert_called_once()

    def test_make_request_with_params(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test _make_request with query parameters."""
        params = {"q": "test"}
        mock_httpx_client.get.return_value.json.return_value = {"result": "data"}

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source._make_request("/search.json", params=params)

        assert result == {"result": "data"}
        call_args = mock_httpx_client.get.call_args
        assert call_args[0][0] == "https://test.openlibrary.org/search.json"
        assert call_args[1]["params"] == params

    def test_make_request_404(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test _make_request with 404 response."""
        response = MagicMock()
        response.status_code = 404
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=response
        )
        mock_httpx_client.get.return_value = response

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceNotFoundError, match="Resource not found"),
        ):
            data_source._make_request("/missing.json")

    def test_make_request_429(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test _make_request with 429 response."""
        response = MagicMock()
        response.status_code = 429
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limit", request=MagicMock(), response=response
        )
        mock_httpx_client.get.return_value = response

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceRateLimitError, match="rate limit exceeded"),
        ):
            data_source._make_request("/test.json")

    def test_make_request_429_before_raise(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test _make_request with 429 status code before raise_for_status."""
        response = MagicMock()
        response.status_code = 429
        response.raise_for_status.return_value = None
        mock_httpx_client.get.return_value = response

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceRateLimitError),
        ):
            data_source._make_request("/test.json")

    def test_make_request_404_before_raise(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test _make_request with 404 status code before raise_for_status."""
        response = MagicMock()
        response.status_code = 404
        response.raise_for_status.return_value = None
        mock_httpx_client.get.return_value = response

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceNotFoundError),
        ):
            data_source._make_request("/test.json")

    def test_make_request_http_error(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test _make_request with HTTP error."""
        response = MagicMock()
        response.status_code = 500
        response.text = "Internal Server Error"
        error = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=response
        )
        response.raise_for_status.side_effect = error
        mock_httpx_client.get.return_value = response

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceNetworkError, match="HTTP error 500"),
        ):
            data_source._make_request("/test.json")

    def test_make_request_network_error(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test _make_request with network error."""
        error = httpx.RequestError("Connection failed")
        mock_httpx_client.get.side_effect = error

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceNetworkError, match="Network error"),
        ):
            data_source._make_request("/test.json")


class TestOpenLibraryDataSourceExtractIdentifiers:
    """Test OpenLibraryDataSource _extract_identifiers."""

    @pytest.mark.parametrize(
        ("remote_ids", "expected"),
        [
            ({}, IdentifierDict()),
            (
                {"viaf": "123", "goodreads": "456"},
                IdentifierDict(viaf="123", goodreads="456"),
            ),
            (
                {
                    "viaf": "123",
                    "goodreads": "456",
                    "wikidata": "Q789",
                    "isni": "0000000123456789",
                    "librarything": "LT123",
                    "amazon": "B00ABC",
                    "imdb": "nm123",
                    "musicbrainz": "mb123",
                    "lc_naf": "n123",
                    "opac_sbn": "SBN123",
                    "storygraph": "sg123",
                },
                IdentifierDict(
                    viaf="123",
                    goodreads="456",
                    wikidata="Q789",
                    isni="0000000123456789",
                    librarything="LT123",
                    amazon="B00ABC",
                    imdb="nm123",
                    musicbrainz="mb123",
                    lc_naf="n123",
                    opac_sbn="SBN123",
                    storygraph="sg123",
                ),
            ),
        ],
    )
    def test_extract_identifiers(
        self,
        remote_ids: dict[str, str],
        expected: IdentifierDict,
        data_source: OpenLibraryDataSource,
    ) -> None:
        """Test _extract_identifiers."""
        data = {"remote_ids": remote_ids}

        result = data_source._extract_identifiers(data)

        assert result == expected

    def test_extract_identifiers_missing_remote_ids(
        self, data_source: OpenLibraryDataSource
    ) -> None:
        """Test _extract_identifiers with missing remote_ids."""
        data = {}

        result = data_source._extract_identifiers(data)

        assert result == IdentifierDict()


class TestOpenLibraryDataSourceExtractBio:
    """Test OpenLibraryDataSource _extract_bio."""

    @pytest.mark.parametrize(
        ("bio", "expected"),
        [
            (None, None),
            ({"value": "Test biography"}, "Test biography"),
            ("Simple string bio", "Simple string bio"),
            ({"other": "key"}, None),
            ({}, None),
        ],
    )
    def test_extract_bio(
        self, bio: object, expected: str | None, data_source: OpenLibraryDataSource
    ) -> None:
        """Test _extract_bio."""
        data = {"bio": bio}

        result = data_source._extract_bio(data)

        assert result == expected


class TestOpenLibraryDataSourceGetPhotoUrl:
    """Test OpenLibraryDataSource _get_photo_url."""

    def test_get_photo_url(self, data_source: OpenLibraryDataSource) -> None:
        """Test _get_photo_url."""
        result = data_source._get_photo_url(12345)

        assert result == f"{OPENLIBRARY_COVERS_BASE}/a/id/12345-L.jpg"


class TestOpenLibraryDataSourceSearchAuthor:
    """Test OpenLibraryDataSource search_author."""

    def test_search_author_success(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test search_author with successful response."""
        mock_httpx_client.get.return_value.json.return_value = {
            "docs": [
                {
                    "key": "/authors/OL123A",
                    "name": "Test Author",
                    "personal_name": "Author",
                    "birth_date": "1950-01-01",
                    "death_date": "2020-01-01",
                    "type": {"key": "/type/author"},
                    "work_count": 10,
                    "ratings_average": 4.5,
                    "ratings_count": 100,
                    "top_work": "Test Book",
                    "photos": [12345],
                    "top_subjects": ["Fiction"],
                }
            ]
        }

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.search_author("Test Author")

        assert len(result) == 1
        assert result[0].key == "OL123A"
        assert result[0].name == "Test Author"

    def test_search_author_with_identifiers(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test search_author with identifiers (should fall through to name search)."""
        identifiers = IdentifierDict(viaf="123", goodreads="456")
        mock_httpx_client.get.return_value.json.return_value = {"docs": []}

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.search_author("Test Author", identifiers=identifiers)

        assert result == []

    def test_search_author_empty_key(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test search_author skips docs with empty key."""
        mock_httpx_client.get.return_value.json.return_value = {
            "docs": [{"key": ""}, {"key": "/authors/OL123A", "name": "Test Author"}]
        }

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.search_author("Test Author")

        assert len(result) == 1
        assert result[0].key == "OL123A"

    def test_search_author_filters_photo_ids(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test search_author filters invalid photo IDs."""
        mock_httpx_client.get.return_value.json.return_value = {
            "docs": [
                {
                    "key": "/authors/OL123A",
                    "name": "Test Author",
                    "photos": [12345, -1, 0, "invalid", 67890],
                }
            ]
        }

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.search_author("Test Author")

        assert result[0].photo_ids == [12345, 67890]

    def test_search_author_network_error(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test search_author raises DataSourceNetworkError on network error."""
        error = httpx.RequestError("Connection failed")
        mock_httpx_client.get.side_effect = error

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceNetworkError),
        ):
            data_source.search_author("Test Author")

    def test_search_author_rate_limit_error(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test search_author raises DataSourceRateLimitError on rate limit."""
        response = MagicMock()
        response.status_code = 429
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limit", request=MagicMock(), response=response
        )
        mock_httpx_client.get.return_value = response

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceRateLimitError),
        ):
            data_source.search_author("Test Author")

    def test_search_author_generic_exception(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test search_author handles generic exceptions."""
        mock_httpx_client.get.side_effect = ValueError("Unexpected error")

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceNetworkError, match="Error searching authors"),
        ):
            data_source.search_author("Test Author")


class TestOpenLibraryDataSourceGetAuthorWorks:
    """Test OpenLibraryDataSource get_author_works."""

    def test_get_author_works_no_limit(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test get_author_works without limit."""
        mock_httpx_client.get.return_value.json.return_value = {
            "docs": [{"key": "/works/OL1W"}],
            "numFound": 1,
        }

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.get_author_works("OL123A")

        assert result == ["OL1W"]

    def test_get_author_works_with_limit(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test get_author_works with limit."""
        mock_httpx_client.get.return_value.json.return_value = {
            "docs": [{"key": "/works/OL1W"} for _ in range(100)],
            "numFound": 1000,
        }

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.get_author_works("OL123A", limit=50)

        assert len(result) == 50

    def test_get_author_works_custom_lang(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test get_author_works with custom language."""
        mock_httpx_client.get.return_value.json.return_value = {
            "docs": [],
            "numFound": 0,
        }

        with patch("httpx.Client", return_value=mock_httpx_client):
            data_source.get_author_works("OL123A", lang="fra")

        # Verify lang parameter was used in request
        call_args = mock_httpx_client.get.call_args
        assert call_args is not None
        _, kwargs = call_args
        assert kwargs["params"]["lang"] == "fra"

    def test_get_author_works_network_error(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test get_author_works raises DataSourceNetworkError on network error."""
        error = httpx.RequestError("Connection failed")
        mock_httpx_client.get.side_effect = error

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceNetworkError),
        ):
            data_source.get_author_works("OL123A")

    def test_get_author_works_rate_limit_error(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test get_author_works raises DataSourceRateLimitError on rate limit."""
        response = MagicMock()
        response.status_code = 429
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limit", request=MagicMock(), response=response
        )
        mock_httpx_client.get.return_value = response

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceRateLimitError),
        ):
            data_source.get_author_works("OL123A")

    def test_get_author_works_generic_exception(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test get_author_works handles generic exceptions."""
        mock_httpx_client.get.side_effect = ValueError("Unexpected error")

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceNetworkError, match="Error fetching author works"),
        ):
            data_source.get_author_works("OL123A")


class TestOpenLibraryDataSourceGetAuthor:
    """Test OpenLibraryDataSource get_author."""

    def test_get_author_success(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
        sample_author_data: dict[str, object],
    ) -> None:
        """Test get_author with successful response."""
        mock_httpx_client.get.return_value.json.return_value = sample_author_data

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.get_author("OL123A")

        assert result is not None
        assert result.key == "OL123A"
        assert result.name == "Test Author"
        assert result.biography == "Test biography"

    def test_get_author_normalizes_key(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
        sample_author_data: dict[str, object],
    ) -> None:
        """Test get_author normalizes key."""
        mock_httpx_client.get.return_value.json.return_value = sample_author_data

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.get_author("/authors/OL123A")

        assert result is not None
        assert result.key == "OL123A"

    def test_get_author_not_found(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test get_author returns None when not found."""
        response = MagicMock()
        response.status_code = 404
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=response
        )
        mock_httpx_client.get.return_value = response

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.get_author("OL123A")

        assert result is None

    def test_get_author_extracts_subjects(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test get_author extracts subjects from top_subjects or subjects."""
        data = {
            "key": "/authors/OL123A",
            "name": "Test Author",
            "top_subjects": ["Fiction"],
        }
        mock_httpx_client.get.return_value.json.return_value = data

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.get_author("OL123A")

        assert result is not None
        assert result.subjects == ["Fiction"]

    def test_get_author_falls_back_to_subjects(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test get_author falls back to subjects when top_subjects is empty."""
        data = {
            "key": "/authors/OL123A",
            "name": "Test Author",
            "top_subjects": [],
            "subjects": ["Science Fiction"],
        }
        mock_httpx_client.get.return_value.json.return_value = data

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.get_author("OL123A")

        assert result is not None
        assert result.subjects == ["Science Fiction"]

    def test_get_author_network_error(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test get_author raises DataSourceNetworkError on network error."""
        error = httpx.RequestError("Connection failed")
        mock_httpx_client.get.side_effect = error

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceNetworkError),
        ):
            data_source.get_author("OL123A")

    def test_get_author_rate_limit_error(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test get_author raises DataSourceRateLimitError on rate limit."""
        response = MagicMock()
        response.status_code = 429
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limit", request=MagicMock(), response=response
        )
        mock_httpx_client.get.return_value = response

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceRateLimitError),
        ):
            data_source.get_author("OL123A")

    def test_get_author_generic_exception(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test get_author handles generic exceptions."""
        mock_httpx_client.get.side_effect = ValueError("Unexpected error")

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceNetworkError, match="Error fetching author"),
        ):
            data_source.get_author("OL123A")


class TestOpenLibraryDataSourceExtractBookFromDoc:
    """Test OpenLibraryDataSource _extract_book_from_doc."""

    @pytest.mark.parametrize(
        ("doc", "expected_key"),
        [
            ({"key": "/works/OL123W"}, "OL123W"),
            ({"key": "/books/OL456M"}, "OL456M"),
            ({"key": ""}, None),
            ({}, None),
        ],
    )
    def test_extract_book_from_doc(
        self,
        doc: dict[str, object],
        expected_key: str | None,
        data_source: OpenLibraryDataSource,
    ) -> None:
        """Test _extract_book_from_doc."""
        result = data_source._extract_book_from_doc(doc)

        if expected_key is None:
            assert result is None
        else:
            assert result is not None
            assert result.key == expected_key

    def test_extract_book_from_doc_full(
        self,
        data_source: OpenLibraryDataSource,
        sample_search_doc: dict[str, object],
    ) -> None:
        """Test _extract_book_from_doc with full data."""
        result = data_source._extract_book_from_doc(sample_search_doc)

        assert result is not None
        assert result.key == "OL123W"
        assert result.title == "Test Book"
        assert result.authors == ["Test Author"]
        assert result.isbn == "1234567890"
        assert result.isbn13 == "9781234567890"
        assert result.cover_url == f"{OPENLIBRARY_COVERS_BASE}/b/id/12345-L.jpg"

    def test_extract_book_from_doc_no_cover(
        self, data_source: OpenLibraryDataSource
    ) -> None:
        """Test _extract_book_from_doc without cover."""
        doc = {"key": "/works/OL123W", "title": "Test Book"}

        result = data_source._extract_book_from_doc(doc)

        assert result is not None
        assert result.cover_url is None

    def test_extract_book_from_doc_single_isbn(
        self, data_source: OpenLibraryDataSource
    ) -> None:
        """Test _extract_book_from_doc with single ISBN."""
        doc = {"key": "/works/OL123W", "isbn": ["1234567890"]}

        result = data_source._extract_book_from_doc(doc)

        assert result is not None
        assert result.isbn == "1234567890"
        assert result.isbn13 is None


class TestOpenLibraryDataSourceSearchBook:
    """Test OpenLibraryDataSource search_book."""

    def test_search_book_by_title(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
        sample_search_doc: dict[str, object],
    ) -> None:
        """Test search_book by title."""
        mock_httpx_client.get.return_value.json.return_value = {
            "docs": [sample_search_doc]
        }

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.search_book(title="Test Book")

        assert len(result) == 1
        assert result[0].title == "Test Book"

    def test_search_book_by_isbn(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
        sample_search_doc: dict[str, object],
    ) -> None:
        """Test search_book by ISBN."""
        mock_httpx_client.get.return_value.json.return_value = {
            "docs": [sample_search_doc]
        }

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.search_book(isbn="1234567890")

        assert len(result) == 1

    def test_search_book_by_authors(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
        sample_search_doc: dict[str, object],
    ) -> None:
        """Test search_book by authors."""
        mock_httpx_client.get.return_value.json.return_value = {
            "docs": [sample_search_doc]
        }

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.search_book(authors=["Test Author"])

        assert len(result) == 1

    def test_search_book_no_params(
        self, data_source: OpenLibraryDataSource, mock_httpx_client: MagicMock
    ) -> None:
        """Test search_book with no parameters."""
        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.search_book()

        assert result == []
        mock_httpx_client.get.assert_not_called()

    def test_search_book_empty_docs(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test search_book with empty docs."""
        mock_httpx_client.get.return_value.json.return_value = {"docs": []}

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.search_book(title="Test")

        assert result == []

    def test_search_book_skips_invalid_docs(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test search_book skips docs without key."""
        mock_httpx_client.get.return_value.json.return_value = {
            "docs": [{"key": ""}, {"key": "/works/OL123W", "title": "Test"}]
        }

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.search_book(title="Test")

        assert len(result) == 1

    def test_search_book_network_error(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test search_book raises DataSourceNetworkError on network error."""
        error = httpx.RequestError("Connection failed")
        mock_httpx_client.get.side_effect = error

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceNetworkError),
        ):
            data_source.search_book(title="Test")

    def test_search_book_rate_limit_error(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test search_book raises DataSourceRateLimitError on rate limit."""
        response = MagicMock()
        response.status_code = 429
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limit", request=MagicMock(), response=response
        )
        mock_httpx_client.get.return_value = response

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceRateLimitError),
        ):
            data_source.search_book(title="Test")

    def test_search_book_generic_exception(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test search_book handles generic exceptions."""
        mock_httpx_client.get.side_effect = ValueError("Unexpected error")

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceNetworkError, match="Error searching books"),
        ):
            data_source.search_book(title="Test")


class TestOpenLibraryDataSourceExtractAuthorsFromBookData:
    """Test OpenLibraryDataSource _extract_authors_from_book_data."""

    def test_extract_authors_from_book_data_success(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test _extract_authors_from_book_data with successful author fetch."""
        book_data = {
            "authors": [
                {"author": {"key": "/authors/OL123A"}},
                {"author": {"key": "/authors/OL456A"}},
            ]
        }
        mock_httpx_client.get.return_value.json.side_effect = [
            {"name": "Author 1"},
            {"name": "Author 2"},
        ]

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source._extract_authors_from_book_data(book_data)

        assert result == ["Author 1", "Author 2"]

    def test_extract_authors_from_book_data_handles_errors(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test _extract_authors_from_book_data handles author fetch errors."""
        book_data = {
            "authors": [
                {"author": {"key": "/authors/OL123A"}},
                {"author": {"key": "/authors/OL456A"}},
            ]
        }
        # First call raises error, second call succeeds
        response1 = MagicMock()
        response1.status_code = 404
        response1.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=response1
        )

        response2 = MagicMock()
        response2.status_code = 200
        response2.json.return_value = {"name": "Author 2"}
        response2.raise_for_status.return_value = None

        mock_httpx_client.get.side_effect = [response1, response2]

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source._extract_authors_from_book_data(book_data)

        assert result == ["Author 2"]

    def test_extract_authors_from_book_data_empty(
        self, data_source: OpenLibraryDataSource
    ) -> None:
        """Test _extract_authors_from_book_data with empty authors."""
        result = data_source._extract_authors_from_book_data({})

        assert result == []

    def test_extract_authors_from_book_data_invalid_structure(
        self, data_source: OpenLibraryDataSource
    ) -> None:
        """Test _extract_authors_from_book_data with invalid structure."""
        book_data = {"authors": [{"invalid": "structure"}]}

        result = data_source._extract_authors_from_book_data(book_data)

        assert result == []


class TestOpenLibraryDataSourceExtractIsbnsFromBookData:
    """Test OpenLibraryDataSource _extract_isbns_from_book_data."""

    @pytest.mark.parametrize(
        ("identifiers", "expected_isbn_10", "expected_isbn_13"),
        [
            ({}, None, None),
            ({"isbn_10": ["1234567890"]}, "1234567890", None),
            ({"isbn_13": ["9781234567890"]}, None, "9781234567890"),
            (
                {"isbn_10": ["1234567890"], "isbn_13": ["9781234567890"]},
                "1234567890",
                "9781234567890",
            ),
            ({"isbn_10": ["123", "456"]}, "123", None),
            ({"isbn_13": ["978123", "978456"]}, None, "978123"),
        ],
    )
    def test_extract_isbns_from_book_data(
        self,
        identifiers: dict[str, list[str]],
        expected_isbn_10: str | None,
        expected_isbn_13: str | None,
        data_source: OpenLibraryDataSource,
    ) -> None:
        """Test _extract_isbns_from_book_data."""
        data = {"identifiers": identifiers}

        result = data_source._extract_isbns_from_book_data(data)

        assert result == (expected_isbn_10, expected_isbn_13)

    def test_extract_isbns_from_book_data_missing_identifiers(
        self, data_source: OpenLibraryDataSource
    ) -> None:
        """Test _extract_isbns_from_book_data with missing identifiers."""
        result = data_source._extract_isbns_from_book_data({})

        assert result == (None, None)


class TestOpenLibraryDataSourceExtractCoverFromBookData:
    """Test OpenLibraryDataSource _extract_cover_from_book_data."""

    @pytest.mark.parametrize(
        ("covers", "expected"),
        [
            ([], None),
            ([12345], f"{OPENLIBRARY_COVERS_BASE}/b/id/12345-L.jpg"),
            ([12345, 67890], f"{OPENLIBRARY_COVERS_BASE}/b/id/12345-L.jpg"),
        ],
    )
    def test_extract_cover_from_book_data(
        self,
        covers: list[int],
        expected: str | None,
        data_source: OpenLibraryDataSource,
    ) -> None:
        """Test _extract_cover_from_book_data."""
        data = {"covers": covers}

        result = data_source._extract_cover_from_book_data(data)

        assert result == expected

    def test_extract_cover_from_book_data_missing_covers(
        self, data_source: OpenLibraryDataSource
    ) -> None:
        """Test _extract_cover_from_book_data with missing covers."""
        result = data_source._extract_cover_from_book_data({})

        assert result is None


class TestOpenLibraryDataSourceGetBook:
    """Test OpenLibraryDataSource get_book."""

    def test_get_book_success(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
        sample_book_data: dict[str, object],
    ) -> None:
        """Test get_book with successful response."""
        mock_httpx_client.get.return_value.json.side_effect = [
            sample_book_data,
            {"name": "Author 1"},
            {"name": "Author 2"},
        ]

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.get_book("OL123W")

        assert result is not None
        assert result.key == "OL123W"
        assert result.title == "Test Book"

    def test_get_book_normalizes_key(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
        sample_book_data: dict[str, object],
    ) -> None:
        """Test get_book normalizes key."""
        mock_httpx_client.get.return_value.json.return_value = sample_book_data

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.get_book("/works/OL123W")

        assert result is not None
        assert result.key == "OL123W"

    def test_get_book_skip_authors(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
        sample_book_data: dict[str, object],
    ) -> None:
        """Test get_book with skip_authors=True."""
        mock_httpx_client.get.return_value.json.return_value = sample_book_data

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.get_book("OL123W", skip_authors=True)

        assert result is not None
        assert result.authors == []

    def test_get_book_not_found(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test get_book returns None when not found."""
        response = MagicMock()
        response.status_code = 404
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=response
        )
        mock_httpx_client.get.return_value = response

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.get_book("OL123W")

        assert result is None

    def test_get_book_extracts_description_dict(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test get_book extracts description from dict."""
        data = {
            "key": "/works/OL123W",
            "title": "Test Book",
            "description": {"value": "Test description"},
        }
        mock_httpx_client.get.return_value.json.return_value = data

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.get_book("OL123W", skip_authors=True)

        assert result is not None
        assert result.description == "Test description"

    def test_get_book_extracts_subjects(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test get_book extracts subjects in various formats."""
        data = {
            "key": "/works/OL123W",
            "title": "Test Book",
            "subjects": [
                "Fiction",
                {"name": "Science Fiction"},
                {"key": "/subjects/sci-fi"},
            ],
        }
        mock_httpx_client.get.return_value.json.return_value = data

        with patch("httpx.Client", return_value=mock_httpx_client):
            result = data_source.get_book("OL123W", skip_authors=True)

        assert result is not None
        assert "Fiction" in result.subjects
        assert "Science Fiction" in result.subjects

    def test_get_book_network_error(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test get_book raises DataSourceNetworkError on network error."""
        error = httpx.RequestError("Connection failed")
        mock_httpx_client.get.side_effect = error

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceNetworkError),
        ):
            data_source.get_book("OL123W")

    def test_get_book_rate_limit_error(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test get_book raises DataSourceRateLimitError on rate limit."""
        response = MagicMock()
        response.status_code = 429
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limit", request=MagicMock(), response=response
        )
        mock_httpx_client.get.return_value = response

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceRateLimitError),
        ):
            data_source.get_book("OL123W")

    def test_get_book_generic_exception(
        self,
        data_source: OpenLibraryDataSource,
        mock_httpx_client: MagicMock,
    ) -> None:
        """Test get_book handles generic exceptions."""
        mock_httpx_client.get.side_effect = ValueError("Unexpected error")

        with (
            patch("httpx.Client", return_value=mock_httpx_client),
            pytest.raises(DataSourceNetworkError, match="Error fetching book"),
        ):
            data_source.get_book("OL123W")
