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

"""OpenLibrary local dump data source implementation."""

import json
import logging
import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from fundamental.services.library_scanning.data_sources.base import (
    BaseDataSource,
    DataSourceNotFoundError,
)
from fundamental.services.library_scanning.data_sources.types import (
    AuthorData,
    BookData,
    IdentifierDict,
)

logger = logging.getLogger(__name__)

OPENLIBRARY_COVERS_BASE = "https://covers.openlibrary.org"


class OpenLibraryDumpDataSource(BaseDataSource):
    """Data source using local OpenLibrary dump SQLite database.

    Queries a locally ingested SQLite database instead of the live API.
    Suitable for high-volume scanning.
    """

    def __init__(
        self,
        data_directory: str = "/data",
    ) -> None:
        """Initialize dump data source.

        Parameters
        ----------
        data_directory : str
            Path to data directory containing openlibrary/openlibrary.db.
        """
        self.db_path = Path(data_directory) / "openlibrary" / "openlibrary.db"

    @property
    def name(self) -> str:
        """Get data source name."""
        return "OpenLibraryDump"

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection.

        Returns
        -------
        sqlite3.Connection
            Database connection.

        Raises
        ------
        DataSourceNotFoundError
            If database file does not exist.
        """
        if not self.db_path.exists():
            msg = f"OpenLibrary dump DB not found at {self.db_path}"
            raise DataSourceNotFoundError(msg)

        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def _extract_identifiers(self, data: dict[str, Any]) -> IdentifierDict:
        """Extract identifiers from author data."""
        remote_ids = data.get("remote_ids", {})
        return IdentifierDict(
            viaf=remote_ids.get("viaf"),
            goodreads=remote_ids.get("goodreads"),
            wikidata=remote_ids.get("wikidata"),
            isni=remote_ids.get("isni"),
            librarything=remote_ids.get("librarything"),
            amazon=remote_ids.get("amazon"),
            imdb=remote_ids.get("imdb"),
            musicbrainz=remote_ids.get("musicbrainz"),
            lc_naf=remote_ids.get("lc_naf"),
            opac_sbn=remote_ids.get("opac_sbn"),
            storygraph=remote_ids.get("storygraph"),
        )

    def _extract_bio(self, data: dict[str, Any]) -> str | None:
        """Extract biography text."""
        bio = data.get("bio")
        if isinstance(bio, dict):
            return bio.get("value")
        if isinstance(bio, str):
            return bio
        return None

    def _generate_name_permutations(self, name: str) -> list[str]:
        """Generate various name permutations for robust searching.

        Parameters
        ----------
        name : str
            Original author name.

        Returns
        -------
        list[str]
            List of name permutations to search for.
        """
        name = name.strip()
        if not name:
            return []

        permutations = [name]

        # Case variations
        permutations.append(name.lower())
        permutations.append(name.upper())
        permutations.append(name.title())

        # Handle "Last, First" format
        if "," in name:
            parts = [p.strip() for p in name.split(",", 1)]
            if len(parts) == 2:
                last, first = parts
                # "First Last" format
                permutations.append(f"{first} {last}")
                permutations.append(f"{first} {last}".lower())
                permutations.append(f"{first} {last}".title())
                # "Last First" format (without comma)
                permutations.append(f"{last} {first}")
                permutations.append(f"{last} {first}".lower())
                permutations.append(f"{last} {first}".title())

        # Handle "First Last" format - convert to "Last, First"
        else:
            parts = name.split()
            if len(parts) >= 2:
                # Assume last word is last name, rest is first name
                first = " ".join(parts[:-1])
                last = parts[-1]
                # "Last, First" format
                permutations.append(f"{last}, {first}")
                permutations.append(f"{last}, {first}".lower())
                permutations.append(f"{last}, {first}".title())

        # Remove duplicates while preserving order
        seen = set()
        unique_permutations = []
        for perm in permutations:
            if perm and perm not in seen:
                seen.add(perm)
                unique_permutations.append(perm)

        return unique_permutations

    def search_author(
        self,
        name: str,
        identifiers: IdentifierDict | None = None,  # noqa: ARG002
    ) -> Sequence[AuthorData]:
        """Search for authors by name with robust permutation matching.

        Searches across the name column and alternate_names JSON field,
        handling various name formats (e.g., "Brandon Sanderson",
        "Sanderson, Brandon", "brandon sanderson").

        Parameters
        ----------
        name : str
            Author name to search for.
        identifiers : IdentifierDict | None
            Optional identifiers (not used in dump search).

        Returns
        -------
        Sequence[AuthorData]
            List of matching authors.
        """
        # Note: Dump DB currently only indexes name.
        # Identifier search would require additional indexing or
        # full table scan (too slow). We fall back to name search.

        if not name or not name.strip():
            return []

        results: list[AuthorData] = []
        seen_keys: set[str] = set()

        try:
            with self._get_connection() as conn:
                # Generate name permutations for robust matching
                name_permutations = self._generate_name_permutations(name)

                # Build query: search name column with all permutations
                # and also check alternate_names JSON field
                name_conditions = []
                name_params: list[str] = []
                for perm in name_permutations:
                    name_conditions.append("LOWER(name) LIKE LOWER(?)")
                    name_params.append(f"%{perm}%")

                # Also search in alternate_names JSON array
                # Use the original name and a few key permutations for JSON search
                json_search_names = [name, *name_permutations[:3]]
                json_conditions = []
                json_params: list[str] = []
                json_condition_template = (
                    "EXISTS ("
                    "SELECT 1 FROM json_each(data, '$.alternate_names') "
                    "WHERE LOWER(json_each.value) LIKE LOWER(?)"
                    ")"
                )
                for json_name in json_search_names:
                    json_conditions.append(json_condition_template)
                    json_params.append(f"%{json_name}%")

                # Combine conditions: name column OR alternate_names
                all_conditions = name_conditions + json_conditions
                all_params = name_params + json_params

                # Build query safely - conditions are hardcoded strings, only params are dynamic
                where_clause = " OR ".join(all_conditions)
                query = (
                    "SELECT DISTINCT key, data FROM authors "  # noqa: S608
                    "WHERE (" + where_clause + ") "
                    "LIMIT 50"
                )

                cursor = conn.execute(query, all_params)

                for row in cursor:
                    # Avoid duplicates
                    if row["key"] in seen_keys:
                        continue
                    seen_keys.add(row["key"])

                    try:
                        data = json.loads(row["data"])
                        author = self._parse_author_data(row["key"], data)
                        results.append(author)
                    except (json.JSONDecodeError, KeyError):
                        continue

        except DataSourceNotFoundError:
            logger.warning("OpenLibrary dump DB not found, skipping search")
            return []
        except sqlite3.Error:
            logger.exception("Database error searching authors")
            return []

        return results

    def _parse_author_data(self, key: str, data: dict[str, Any]) -> AuthorData:
        """Parse raw JSON data into AuthorData."""
        photos = data.get("photos", [])
        photo_ids = [p for p in photos if isinstance(p, int) and p > 0]

        links = [
            {
                "title": link.get("title", ""),
                "url": link.get("url", ""),
                "type": link.get("type", {}).get("key", ""),
            }
            for link in data.get("links", [])
            if isinstance(link, dict)
        ]

        # Top subjects logic is complex in API, here we just take what's available
        # or we might not have it pre-calculated in the dump.
        # The dump usually contains raw author data, 'top_subjects' is often derived.
        # We'll take direct 'subjects' field if present, or None.
        subjects = data.get("subjects", [])
        # API response usually has top_work etc calculated. Dump might not.

        return AuthorData(
            key=key,
            name=data.get("name", ""),
            personal_name=data.get("personal_name"),
            fuller_name=data.get("fuller_name"),
            title=data.get("title"),
            birth_date=data.get("birth_date"),
            death_date=data.get("death_date"),
            entity_type=data.get("entity_type"),
            biography=self._extract_bio(data),
            photo_ids=photo_ids,
            alternate_names=data.get("alternate_names", []),
            links=links,
            identifiers=self._extract_identifiers(data),
            work_count=None,  # Often not in author dump
            ratings_average=None,
            ratings_count=None,
            top_work=None,
            subjects=subjects,
        )

    def get_author(self, key: str) -> AuthorData | None:
        """Get author by key."""
        try:
            with self._get_connection() as conn:
                # Normalize key
                normalized_key = key.replace("/authors/", "").replace("authors/", "")

                cursor = conn.execute(
                    "SELECT key, data FROM authors WHERE key = ?", (normalized_key,)
                )
                row = cursor.fetchone()

                if not row:
                    return None

                data = json.loads(row["data"])
                return self._parse_author_data(row["key"], data)

        except DataSourceNotFoundError:
            return None
        except (sqlite3.Error, json.JSONDecodeError):
            logger.exception("Error getting author %s", key)
            return None

    def search_book(
        self,
        title: str | None = None,
        isbn: str | None = None,  # noqa: ARG002
        authors: Sequence[str] | None = None,  # noqa: ARG002
    ) -> Sequence[BookData]:
        """Search for books."""
        # Only title search is efficient with current schema
        if not title:
            return []

        results: list[BookData] = []
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT key, data FROM works WHERE title LIKE ? LIMIT 20",
                    (f"%{title}%",),
                )

                for row in cursor:
                    try:
                        data = json.loads(row["data"])
                        book = self._parse_book_data(row["key"], data)
                        results.append(book)
                    except (json.JSONDecodeError, KeyError):
                        continue

        except DataSourceNotFoundError:
            return []
        except sqlite3.Error:
            logger.exception("Database error searching books")
            return []

        return results

    def _parse_book_data(self, key: str, data: dict[str, Any]) -> BookData:
        """Parse raw JSON data into BookData."""
        # Authors in works dump are usually references: {"key": "/authors/OL..."}
        _ = data.get("authors", [])
        # We can't easily resolve names here without extra lookups,
        # so we might just return empty list or keys.
        # The BaseDataSource expects names.
        # Resolving them would require N queries.
        # For now, we skip resolving to keep it fast.
        author_names: list[str] = []

        covers = data.get("covers", [])
        cover_url = None
        if covers:
            cover_url = f"{OPENLIBRARY_COVERS_BASE}/b/id/{covers[0]}-L.jpg"

        description = data.get("description")
        if isinstance(description, dict):
            description = description.get("value")

        subjects = [
            s
            if isinstance(s, str)
            else s.get("name", "")
            if isinstance(s, dict)
            else str(s)
            for s in data.get("subjects", [])
            if s
        ]

        return BookData(
            key=key,
            title=data.get("title", ""),
            authors=author_names,
            isbn=None,  # Works don't usually have ISBNs (Editions do)
            isbn13=None,
            publish_date=data.get("first_publish_date"),
            publishers=[],  # Works don't usually have publishers
            subjects=subjects,
            description=description,
            cover_url=cover_url,
        )

    def get_book(self, key: str, skip_authors: bool = False) -> BookData | None:  # noqa: ARG002
        """Get book by key."""
        try:
            with self._get_connection() as conn:
                normalized_key = key.replace("/works/", "").replace("/books/", "")

                cursor = conn.execute(
                    "SELECT key, data FROM works WHERE key = ?", (normalized_key,)
                )
                row = cursor.fetchone()

                if not row:
                    return None

                data = json.loads(row["data"])
                return self._parse_book_data(row["key"], data)

        except DataSourceNotFoundError:
            return None
        except (sqlite3.Error, json.JSONDecodeError):
            logger.exception("Error getting book %s", key)
            return None
