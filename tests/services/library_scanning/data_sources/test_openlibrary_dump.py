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

"""Tests for OpenLibraryDumpDataSource to achieve 100% coverage."""

import json
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from fundamental.services.library_scanning.data_sources.openlibrary_dump import (
    OPENLIBRARY_COVERS_BASE,
    OpenLibraryDumpDataSource,
)
from fundamental.services.library_scanning.data_sources.types import (
    IdentifierDict,
)


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    """Create a temporary database path.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory path.

    Returns
    -------
    Path
        Path to temporary database file.
    """
    db_dir = tmp_path / "openlibrary"
    db_dir.mkdir(parents=True)
    return db_dir / "openlibrary.db"


@pytest.fixture
def data_source(tmp_path: Path) -> OpenLibraryDumpDataSource:
    """Create OpenLibraryDumpDataSource instance.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory path.

    Returns
    -------
    OpenLibraryDumpDataSource
        Data source instance.
    """
    return OpenLibraryDumpDataSource(data_directory=str(tmp_path))


@pytest.fixture
def sample_author_data() -> dict[str, object]:
    """Create sample author data from dump.

    Returns
    -------
    dict[str, object]
        Sample author data.
    """
    return {
        "key": "OL123A",
        "name": "Test Author",
        "personal_name": "Author",
        "fuller_name": "Test Author",
        "title": "Dr.",
        "birth_date": "1950-01-01",
        "death_date": "2020-01-01",
        "entity_type": {"key": "/type/author"},
        "photos": [12345, 67890],
        "bio": {"value": "Test biography"},
        "alternate_names": ["Alt Name 1", "Alt Name 2"],
        "links": [
            {"title": "Website", "url": "https://example.com", "type": {"key": "web"}}
        ],
        "remote_ids": {
            "viaf": "123456",
            "goodreads": "789012",
            "wikidata": "Q123",
            "isni": "0000000123456789",
            "librarything": "LT123",
            "amazon": "B00ABC",
            "imdb": "nm123",
            "musicbrainz": "mb123",
            "lc_naf": "n123",
            "opac_sbn": "SBN123",
            "storygraph": "sg123",
        },
        "subjects": ["Fiction", "Science Fiction"],
    }


@pytest.fixture
def sample_work_data() -> dict[str, object]:
    """Create sample work data from dump.

    Returns
    -------
    dict[str, object]
        Sample work data.
    """
    return {
        "key": "OL123W",
        "title": "Test Book",
        "authors": [{"key": "/authors/OL123A"}],
        "covers": [12345],
        "first_publish_date": "2020-01-01",
        "subjects": ["Fiction", {"name": "Science Fiction"}],
        "description": {"value": "Test description"},
    }


def create_test_db(
    db_path: Path,
    authors: list[dict[str, object]] | None = None,
    works: list[dict[str, object]] | None = None,
) -> None:
    """Create a test SQLite database.

    Parameters
    ----------
    db_path : Path
        Path to database file.
    authors : list[dict[str, object]] | None
        List of author records to insert.
    works : list[dict[str, object]] | None
        List of work records to insert.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables with name column for authors (used in search queries)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS authors (
            key TEXT PRIMARY KEY,
            name TEXT,
            data TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS works (
            key TEXT PRIMARY KEY,
            title TEXT,
            data TEXT
        )
        """
    )

    # Insert authors
    if authors:
        for author in authors:
            author_data = author["data"]
            if isinstance(author_data, dict):
                author_name = str(author_data.get("name", ""))  # type: ignore[arg-type]
            else:
                author_name = ""
            cursor.execute(
                "INSERT INTO authors (key, name, data) VALUES (?, ?, ?)",
                (author["key"], author_name, json.dumps(author_data)),
            )

    # Insert works
    if works:
        for work in works:
            work_data = work["data"]
            if isinstance(work_data, dict):
                work_title = str(work_data.get("title", ""))  # type: ignore[arg-type]
            else:
                work_title = ""
            cursor.execute(
                "INSERT INTO works (key, title, data) VALUES (?, ?, ?)",
                (work["key"], work_title, json.dumps(work_data)),
            )

    conn.commit()
    conn.close()


class TestOpenLibraryDumpDataSourceInit:
    """Test OpenLibraryDumpDataSource initialization."""

    def test_init_default(self) -> None:
        """Test __init__ with default parameters."""
        source = OpenLibraryDumpDataSource()

        assert source._engine is not None

    def test_init_custom(self, tmp_path: Path) -> None:
        """Test __init__ with custom data_directory.

        Parameters
        ----------
        tmp_path : Path
            Temporary directory path.
        """
        source = OpenLibraryDumpDataSource(data_directory=str(tmp_path))

        assert source._engine is not None

    def test_name_property(self, data_source: OpenLibraryDumpDataSource) -> None:
        """Test name property.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        """
        assert data_source.name == "OpenLibraryDump"


class TestOpenLibraryDumpDataSourceExtractIdentifiers:
    """Test OpenLibraryDumpDataSource._extract_identifiers."""

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
        data_source: OpenLibraryDumpDataSource,
    ) -> None:
        """Test _extract_identifiers.

        Parameters
        ----------
        remote_ids : dict[str, str]
            Remote IDs dictionary.
        expected : IdentifierDict
            Expected result.
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        """
        data = {"remote_ids": remote_ids}

        result = data_source._extract_identifiers(data)

        assert result == expected

    def test_extract_identifiers_missing_remote_ids(
        self, data_source: OpenLibraryDumpDataSource
    ) -> None:
        """Test _extract_identifiers with missing remote_ids.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        """
        data = {}

        result = data_source._extract_identifiers(data)

        assert result == IdentifierDict()


class TestOpenLibraryDumpDataSourceExtractBio:
    """Test OpenLibraryDumpDataSource._extract_bio."""

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
        self,
        bio: object,
        expected: str | None,
        data_source: OpenLibraryDumpDataSource,
    ) -> None:
        """Test _extract_bio.

        Parameters
        ----------
        bio : object
            Bio value.
        expected : str | None
            Expected result.
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        """
        data = {"bio": bio}

        result = data_source._extract_bio(data)

        assert result == expected


class TestOpenLibraryDumpDataSourceGenerateNamePermutations:
    """Test OpenLibraryDumpDataSource._generate_name_permutations.

    Note: This method was removed when migrating from SQLite to PostgreSQL.
    PostgreSQL trigram similarity handles name matching more efficiently.
    These tests are kept for reference but are skipped.
    """

    @pytest.mark.skip(
        reason="Method removed - PostgreSQL trigram similarity handles this"
    )
    @pytest.mark.parametrize(
        ("name", "expected_count", "expected_contains"),
        [
            ("", 0, []),
            ("   ", 0, []),
            (
                "John Doe",
                5,
                ["John Doe", "john doe", "JOHN DOE", "John Doe", "Doe, John"],
            ),
            ("Doe, John", 7, ["Doe, John", "doe, john", "John Doe", "john doe"]),
            ("Single", 3, ["Single", "single", "SINGLE"]),
        ],
    )
    def test_generate_name_permutations(
        self,
        name: str,
        expected_count: int,
        expected_contains: list[str],
        data_source: OpenLibraryDumpDataSource,
    ) -> None:
        """Test _generate_name_permutations.

        Parameters
        ----------
        name : str
            Author name.
        expected_count : int
            Expected number of permutations.
        expected_contains : list[str]
            Expected permutations to be present.
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        """
        result = data_source._generate_name_permutations(name)  # type: ignore[attr-defined]

        assert len(result) == expected_count
        for expected in expected_contains:
            assert expected in result

    @pytest.mark.skip(
        reason="Method removed - PostgreSQL trigram similarity handles this"
    )
    def test_generate_name_permutations_removes_duplicates(
        self, data_source: OpenLibraryDumpDataSource
    ) -> None:
        """Test _generate_name_permutations removes duplicates.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        """
        result = data_source._generate_name_permutations("Test Test")  # type: ignore[attr-defined]

        # Should not have duplicate entries
        assert len(result) == len(set(result))


class TestOpenLibraryDumpDataSourceSearchAuthor:
    """Test OpenLibraryDumpDataSource.search_author."""

    def test_search_author_empty_name(
        self, data_source: OpenLibraryDumpDataSource, tmp_db_path: Path
    ) -> None:
        """Test search_author with empty name.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        """
        create_test_db(tmp_db_path)

        result = data_source.search_author("")

        assert result == []

    def test_search_author_whitespace_name(
        self, data_source: OpenLibraryDumpDataSource, tmp_db_path: Path
    ) -> None:
        """Test search_author with whitespace-only name.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        """
        create_test_db(tmp_db_path)

        result = data_source.search_author("   ")

        assert result == []

    def test_search_author_success(
        self,
        data_source: OpenLibraryDumpDataSource,
        tmp_db_path: Path,
        sample_author_data: dict[str, object],
    ) -> None:
        """Test search_author with successful match.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        sample_author_data : dict[str, object]
            Sample author data.
        """
        create_test_db(
            tmp_db_path,
            authors=[{"key": "OL123A", "data": sample_author_data}],
        )

        result = data_source.search_author("Test Author")

        assert len(result) == 1
        assert result[0].key == "OL123A"
        assert result[0].name == "Test Author"

    def test_search_author_with_alternate_names(
        self,
        data_source: OpenLibraryDumpDataSource,
        tmp_db_path: Path,
        sample_author_data: dict[str, object],
    ) -> None:
        """Test search_author matches alternate names.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        sample_author_data : dict[str, object]
            Sample author data.
        """
        create_test_db(
            tmp_db_path,
            authors=[{"key": "OL123A", "data": sample_author_data}],
        )

        result = data_source.search_author("Alt Name 1")

        assert len(result) == 1
        assert result[0].key == "OL123A"

    def test_search_author_with_identifiers(
        self,
        data_source: OpenLibraryDumpDataSource,
        tmp_db_path: Path,
        sample_author_data: dict[str, object],
    ) -> None:
        """Test search_author with identifiers parameter (ignored in dump).

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        sample_author_data : dict[str, object]
            Sample author data.
        """
        create_test_db(
            tmp_db_path,
            authors=[{"key": "OL123A", "data": sample_author_data}],
        )

        identifiers = IdentifierDict(viaf="123")
        result = data_source.search_author("Test Author", identifiers=identifiers)

        assert len(result) == 1

    def test_search_author_db_not_found(
        self, data_source: OpenLibraryDumpDataSource
    ) -> None:
        """Test search_author when database not found.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        """
        result = data_source.search_author("Test Author")

        assert result == []

    def test_search_author_database_error(
        self, data_source: OpenLibraryDumpDataSource, tmp_db_path: Path
    ) -> None:
        """Test search_author handles database errors.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        """
        create_test_db(tmp_db_path)

        with patch(
            "fundamental.services.library_scanning.data_sources.openlibrary_dump.get_session"
        ) as mock_get_session:
            mock_get_session.side_effect = OperationalError(
                "Database error", None, Exception("Database error")
            )

            result = data_source.search_author("Test Author")

            assert result == []

    def test_search_author_invalid_json(
        self, data_source: OpenLibraryDumpDataSource, tmp_db_path: Path
    ) -> None:
        """Test search_author handles invalid JSON.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        """
        # Note: This test is less relevant with PostgreSQL JSONB,
        # but we keep it to test error handling in _parse_query_results
        # For PostgreSQL, invalid JSON would be caught at insert time
        # So we'll skip this test or mock the data to be invalid
        create_test_db(tmp_db_path)

        # Mock a row with invalid data structure
        from unittest.mock import Mock

        mock_row = Mock()
        mock_row.key = "OL123A"
        mock_row.data = "invalid"  # Not a dict

        with patch(
            "fundamental.services.library_scanning.data_sources.openlibrary_dump.get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_session.exec.return_value.all.return_value = [mock_row]
            mock_get_session.return_value = mock_session

            result = data_source.search_author("Test")

            assert result == []

    def test_search_author_duplicate_keys(
        self,
        data_source: OpenLibraryDumpDataSource,
        tmp_db_path: Path,
        sample_author_data: dict[str, object],
    ) -> None:
        """Test search_author removes duplicate keys.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        sample_author_data : dict[str, object]
            Sample author data.
        """
        # Create database with multiple authors matching the search
        authors = [{"key": f"OL123A_{i}", "data": sample_author_data} for i in range(3)]
        create_test_db(tmp_db_path, authors=authors)

        result = data_source.search_author("Test Author")

        # Should return all unique keys
        assert len(result) == 3

    def test_search_author_duplicate_key_skip(
        self,
        data_source: OpenLibraryDumpDataSource,
        tmp_db_path: Path,
        sample_author_data: dict[str, object],
    ) -> None:
        """Test search_author skips duplicate keys (covers line 250).

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        sample_author_data : dict[str, object]
            Sample author data.
        """
        # Create database with one author
        create_test_db(
            tmp_db_path,
            authors=[{"key": "OL123A", "data": sample_author_data}],
        )

        # Create a custom row class that can return duplicate keys
        class DuplicateRow:
            def __init__(self, key: str, data: str) -> None:
                self._key = key
                self._data = data

            def __getitem__(self, key: str) -> str:
                if key == "key":
                    return self._key
                if key == "data":
                    return self._data
                raise KeyError(key)

        # Mock the session to return duplicate rows
        from unittest.mock import Mock

        row1 = Mock()
        row1.key = "OL123A"
        row1.data = sample_author_data
        row2 = Mock()
        row2.key = "OL123A"  # Same key
        row2.data = sample_author_data

        with patch(
            "fundamental.services.library_scanning.data_sources.openlibrary_dump.get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_session.exec.return_value.all.return_value = [row1, row2]
            mock_get_session.return_value = mock_session

            result = data_source.search_author("Test Author")

            # Should only return one result (duplicate skipped)
            assert len(result) == 1


class TestOpenLibraryDumpDataSourceParseAuthorData:
    """Test OpenLibraryDumpDataSource._parse_author_data."""

    def test_parse_author_data_full(
        self,
        data_source: OpenLibraryDumpDataSource,
        sample_author_data: dict[str, object],
    ) -> None:
        """Test _parse_author_data with full data.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        sample_author_data : dict[str, object]
            Sample author data.
        """
        result = data_source._parse_author_data("OL123A", sample_author_data)

        assert result.key == "OL123A"
        assert result.name == "Test Author"
        assert result.personal_name == "Author"
        assert result.biography == "Test biography"
        assert result.photo_ids == [12345, 67890]
        assert len(result.links) == 1
        assert result.links[0]["title"] == "Website"
        assert result.identifiers is not None
        assert result.identifiers.viaf == "123456"

    def test_parse_author_data_filters_photo_ids(
        self, data_source: OpenLibraryDumpDataSource
    ) -> None:
        """Test _parse_author_data filters invalid photo IDs.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        """
        data = {
            "name": "Test",
            "photos": [12345, -1, 0, "invalid", 67890],
        }

        result = data_source._parse_author_data("OL123A", data)

        assert result.photo_ids == [12345, 67890]

    def test_parse_author_data_minimal(
        self, data_source: OpenLibraryDumpDataSource
    ) -> None:
        """Test _parse_author_data with minimal data.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        """
        data = {"name": "Test Author"}

        result = data_source._parse_author_data("OL123A", data)

        assert result.key == "OL123A"
        assert result.name == "Test Author"
        assert result.photo_ids == []
        assert result.links == []
        assert result.subjects == []

    def test_parse_author_data_filters_invalid_links(
        self, data_source: OpenLibraryDumpDataSource
    ) -> None:
        """Test _parse_author_data filters invalid links.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        """
        data = {
            "name": "Test",
            "links": [
                {
                    "title": "Valid",
                    "url": "https://example.com",
                    "type": {"key": "web"},
                },
                "invalid",  # Not a dict, should be filtered
                {"title": "No URL"},  # Dict but will be included with empty url
            ],
        }

        result = data_source._parse_author_data("OL123A", data)

        # Only dict links are included (non-dict items are filtered)
        assert len(result.links) == 2
        assert result.links[0]["title"] == "Valid"
        assert result.links[0]["url"] == "https://example.com"
        assert result.links[1]["title"] == "No URL"
        assert result.links[1]["url"] == ""  # Empty string for missing url


class TestOpenLibraryDumpDataSourceGetAuthor:
    """Test OpenLibraryDumpDataSource.get_author."""

    def test_get_author_success(
        self,
        data_source: OpenLibraryDumpDataSource,
        tmp_db_path: Path,
        sample_author_data: dict[str, object],
    ) -> None:
        """Test get_author with successful match.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        sample_author_data : dict[str, object]
            Sample author data.
        """
        create_test_db(
            tmp_db_path,
            authors=[{"key": "OL123A", "data": sample_author_data}],
        )

        result = data_source.get_author("OL123A")

        assert result is not None
        assert result.key == "OL123A"
        assert result.name == "Test Author"

    def test_get_author_normalizes_key(
        self,
        data_source: OpenLibraryDumpDataSource,
        tmp_db_path: Path,
        sample_author_data: dict[str, object],
    ) -> None:
        """Test get_author normalizes key.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        sample_author_data : dict[str, object]
            Sample author data.
        """
        create_test_db(
            tmp_db_path,
            authors=[{"key": "OL123A", "data": sample_author_data}],
        )

        result = data_source.get_author("/authors/OL123A")

        assert result is not None
        assert result.key == "OL123A"

    def test_get_author_not_found(
        self, data_source: OpenLibraryDumpDataSource, tmp_db_path: Path
    ) -> None:
        """Test get_author when author not found.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        """
        create_test_db(tmp_db_path)

        result = data_source.get_author("OL999A")

        assert result is None

    def test_get_author_db_not_found(
        self, data_source: OpenLibraryDumpDataSource
    ) -> None:
        """Test get_author when database not found.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        """
        result = data_source.get_author("OL123A")

        assert result is None

    def test_get_author_database_error(
        self, data_source: OpenLibraryDumpDataSource, tmp_db_path: Path
    ) -> None:
        """Test get_author handles database errors.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        """
        create_test_db(tmp_db_path)

        with patch(
            "fundamental.services.library_scanning.data_sources.openlibrary_dump.get_session"
        ) as mock_get_session:
            mock_get_session.side_effect = OperationalError(
                "Database error", None, Exception("Database error")
            )

            result = data_source.get_author("OL123A")

            assert result is None

    def test_get_author_invalid_json(
        self, data_source: OpenLibraryDumpDataSource, tmp_db_path: Path
    ) -> None:
        """Test get_author handles invalid JSON.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        """
        # Note: With PostgreSQL JSONB, invalid JSON would be caught at insert time
        # This test mocks invalid data structure instead
        from unittest.mock import Mock

        mock_row = Mock()
        mock_row.key = "OL123A"
        mock_row.data = "invalid"  # Not a dict

        with patch(
            "fundamental.services.library_scanning.data_sources.openlibrary_dump.get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_session.exec.return_value.first.return_value = mock_row
            mock_get_session.return_value = mock_session

            result = data_source.get_author("OL123A")

            assert result is None


class TestOpenLibraryDumpDataSourceSearchBook:
    """Test OpenLibraryDumpDataSource.search_book."""

    def test_search_book_no_title(
        self, data_source: OpenLibraryDumpDataSource, tmp_db_path: Path
    ) -> None:
        """Test search_book with no title.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        """
        create_test_db(tmp_db_path)

        result = data_source.search_book()

        assert result == []

    def test_search_book_success(
        self,
        data_source: OpenLibraryDumpDataSource,
        tmp_db_path: Path,
        sample_work_data: dict[str, object],
    ) -> None:
        """Test search_book with successful match.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        sample_work_data : dict[str, object]
            Sample work data.
        """
        create_test_db(
            tmp_db_path,
            works=[{"key": "OL123W", "data": sample_work_data}],
        )

        result = data_source.search_book(title="Test Book")

        assert len(result) == 1
        assert result[0].key == "OL123W"
        assert result[0].title == "Test Book"

    def test_search_book_with_isbn(
        self,
        data_source: OpenLibraryDumpDataSource,
        tmp_db_path: Path,
        sample_work_data: dict[str, object],
    ) -> None:
        """Test search_book with ISBN parameter (ignored in dump).

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        sample_work_data : dict[str, object]
            Sample work data.
        """
        create_test_db(
            tmp_db_path,
            works=[{"key": "OL123W", "data": sample_work_data}],
        )

        result = data_source.search_book(title="Test", isbn="1234567890")

        assert len(result) == 1

    def test_search_book_with_authors(
        self,
        data_source: OpenLibraryDumpDataSource,
        tmp_db_path: Path,
        sample_work_data: dict[str, object],
    ) -> None:
        """Test search_book with authors parameter (ignored in dump).

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        sample_work_data : dict[str, object]
            Sample work data.
        """
        create_test_db(
            tmp_db_path,
            works=[{"key": "OL123W", "data": sample_work_data}],
        )

        result = data_source.search_book(title="Test", authors=["Test Author"])

        assert len(result) == 1

    def test_search_book_db_not_found(
        self, data_source: OpenLibraryDumpDataSource
    ) -> None:
        """Test search_book when database not found.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        """
        result = data_source.search_book(title="Test")

        assert result == []

    def test_search_book_database_error(
        self, data_source: OpenLibraryDumpDataSource, tmp_db_path: Path
    ) -> None:
        """Test search_book handles database errors.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        """
        create_test_db(tmp_db_path)

        with patch(
            "fundamental.services.library_scanning.data_sources.openlibrary_dump.get_session"
        ) as mock_get_session:
            mock_get_session.side_effect = OperationalError(
                "Database error", None, Exception("Database error")
            )

            result = data_source.search_book(title="Test")

            assert result == []

    def test_search_book_invalid_json(
        self, data_source: OpenLibraryDumpDataSource, tmp_db_path: Path
    ) -> None:
        """Test search_book handles invalid JSON.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        """
        # Note: With PostgreSQL JSONB, invalid JSON would be caught at insert time
        # This test mocks invalid data structure instead
        from unittest.mock import Mock

        mock_row = Mock()
        mock_row.key = "OL123W"
        mock_row.data = "invalid"  # Not a dict

        with patch(
            "fundamental.services.library_scanning.data_sources.openlibrary_dump.get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_session.exec.return_value.all.return_value = [mock_row]
            mock_get_session.return_value = mock_session

            result = data_source.search_book(title="Test")

            assert result == []

    def test_search_author_handles_keyerror(
        self,
        data_source: OpenLibraryDumpDataSource,
        tmp_db_path: Path,
        sample_author_data: dict[str, object],
    ) -> None:
        """Test search_author handles KeyError in _parse_author_data (covers line 258).

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        sample_author_data : dict[str, object]
            Sample author data.
        """
        create_test_db(
            tmp_db_path,
            authors=[{"key": "OL123A", "data": sample_author_data}],
        )

        # Patch _parse_author_data to raise KeyError
        with patch.object(
            data_source, "_parse_author_data", side_effect=KeyError("test")
        ):
            result = data_source.search_author("Test Author")

            # Should handle the error gracefully and continue
            assert result == []

    def test_search_book_handles_keyerror(
        self,
        data_source: OpenLibraryDumpDataSource,
        tmp_db_path: Path,
        sample_work_data: dict[str, object],
    ) -> None:
        """Test search_book handles KeyError in _parse_book_data (covers lines 360-361).

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        sample_work_data : dict[str, object]
            Sample work data.
        """
        create_test_db(
            tmp_db_path,
            works=[{"key": "OL123W", "data": sample_work_data}],
        )

        # Patch _parse_book_data to raise KeyError
        with patch.object(
            data_source, "_parse_book_data", side_effect=KeyError("test")
        ):
            result = data_source.search_book(title="Test")

            # Should handle the error gracefully and continue
            assert result == []


class TestOpenLibraryDumpDataSourceParseBookData:
    """Test OpenLibraryDumpDataSource._parse_book_data."""

    def test_parse_book_data_full(
        self,
        data_source: OpenLibraryDumpDataSource,
        sample_work_data: dict[str, object],
    ) -> None:
        """Test _parse_book_data with full data.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        sample_work_data : dict[str, object]
            Sample work data.
        """
        result = data_source._parse_book_data("OL123W", sample_work_data)

        assert result.key == "OL123W"
        assert result.title == "Test Book"
        assert result.authors == []
        assert result.isbn is None
        assert result.isbn13 is None
        assert result.publish_date == "2020-01-01"
        assert result.publishers == []
        assert len(result.subjects) == 2
        assert "Fiction" in result.subjects
        assert "Science Fiction" in result.subjects
        assert result.description == "Test description"
        assert result.cover_url == f"{OPENLIBRARY_COVERS_BASE}/b/id/12345-L.jpg"

    def test_parse_book_data_minimal(
        self, data_source: OpenLibraryDumpDataSource
    ) -> None:
        """Test _parse_book_data with minimal data.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        """
        data = {"title": "Test Book"}

        result = data_source._parse_book_data("OL123W", data)

        assert result.key == "OL123W"
        assert result.title == "Test Book"
        assert result.authors == []
        assert result.cover_url is None
        assert result.description is None
        assert result.subjects == []

    def test_parse_book_data_description_string(
        self, data_source: OpenLibraryDumpDataSource
    ) -> None:
        """Test _parse_book_data with string description.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        """
        data = {"title": "Test", "description": "Simple string"}

        result = data_source._parse_book_data("OL123W", data)

        assert result.description == "Simple string"

    def test_parse_book_data_subjects_various_formats(
        self, data_source: OpenLibraryDumpDataSource
    ) -> None:
        """Test _parse_book_data handles various subject formats.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        """
        data = {
            "title": "Test",
            "subjects": [
                "Fiction",
                {"name": "Science Fiction"},
                {"key": "/subjects/sci-fi"},
                "",
                None,
            ],
        }

        result = data_source._parse_book_data("OL123W", data)

        assert "Fiction" in result.subjects
        assert "Science Fiction" in result.subjects
        assert "" in result.subjects  # Empty string is included
        # None and dict without 'name' are filtered out


class TestOpenLibraryDumpDataSourceGetBook:
    """Test OpenLibraryDumpDataSource.get_book."""

    def test_get_book_success(
        self,
        data_source: OpenLibraryDumpDataSource,
        tmp_db_path: Path,
        sample_work_data: dict[str, object],
    ) -> None:
        """Test get_book with successful match.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        sample_work_data : dict[str, object]
            Sample work data.
        """
        create_test_db(
            tmp_db_path,
            works=[{"key": "OL123W", "data": sample_work_data}],
        )

        result = data_source.get_book("OL123W")

        assert result is not None
        assert result.key == "OL123W"
        assert result.title == "Test Book"

    def test_get_book_normalizes_key(
        self,
        data_source: OpenLibraryDumpDataSource,
        tmp_db_path: Path,
        sample_work_data: dict[str, object],
    ) -> None:
        """Test get_book normalizes key.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        sample_work_data : dict[str, object]
            Sample work data.
        """
        create_test_db(
            tmp_db_path,
            works=[{"key": "OL123W", "data": sample_work_data}],
        )

        result = data_source.get_book("/works/OL123W")

        assert result is not None
        assert result.key == "OL123W"

    def test_get_book_normalizes_books_key(
        self,
        data_source: OpenLibraryDumpDataSource,
        tmp_db_path: Path,
        sample_work_data: dict[str, object],
    ) -> None:
        """Test get_book normalizes /books/ key.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        sample_work_data : dict[str, object]
            Sample work data.
        """
        create_test_db(
            tmp_db_path,
            works=[{"key": "OL123W", "data": sample_work_data}],
        )

        result = data_source.get_book("/books/OL123W")

        assert result is not None
        assert result.key == "OL123W"

    def test_get_book_skip_authors(
        self,
        data_source: OpenLibraryDumpDataSource,
        tmp_db_path: Path,
        sample_work_data: dict[str, object],
    ) -> None:
        """Test get_book with skip_authors parameter.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        sample_work_data : dict[str, object]
            Sample work data.
        """
        create_test_db(
            tmp_db_path,
            works=[{"key": "OL123W", "data": sample_work_data}],
        )

        result = data_source.get_book("OL123W", skip_authors=True)

        assert result is not None
        assert result.authors == []

    def test_get_book_not_found(
        self, data_source: OpenLibraryDumpDataSource, tmp_db_path: Path
    ) -> None:
        """Test get_book when book not found.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        """
        create_test_db(tmp_db_path)

        result = data_source.get_book("OL999W")

        assert result is None

    def test_get_book_db_not_found(
        self, data_source: OpenLibraryDumpDataSource
    ) -> None:
        """Test get_book when database not found.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        """
        result = data_source.get_book("OL123W")

        assert result is None

    def test_get_book_database_error(
        self, data_source: OpenLibraryDumpDataSource, tmp_db_path: Path
    ) -> None:
        """Test get_book handles database errors.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        """
        create_test_db(tmp_db_path)

        with patch(
            "fundamental.services.library_scanning.data_sources.openlibrary_dump.get_session"
        ) as mock_get_session:
            mock_get_session.side_effect = OperationalError(
                "Database error", None, Exception("Database error")
            )

            result = data_source.get_book("OL123W")

            assert result is None

    def test_get_book_invalid_json(
        self, data_source: OpenLibraryDumpDataSource, tmp_db_path: Path
    ) -> None:
        """Test get_book handles invalid JSON.

        Parameters
        ----------
        data_source : OpenLibraryDumpDataSource
            Data source instance.
        tmp_db_path : Path
            Temporary database path.
        """
        # Note: With PostgreSQL JSONB, invalid JSON would be caught at insert time
        # This test mocks invalid data structure instead
        from unittest.mock import Mock

        mock_row = Mock()
        mock_row.key = "OL123W"
        mock_row.data = "invalid"  # Not a dict

        with patch(
            "fundamental.services.library_scanning.data_sources.openlibrary_dump.get_session"
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_session.exec.return_value.first.return_value = mock_row
            mock_get_session.return_value = mock_session

            result = data_source.get_book("OL123W")

            assert result is None
