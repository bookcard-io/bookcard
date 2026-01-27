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

"""Book matching service for read list imports.

Matches BookReference objects to actual books in the library using
exact, fuzzy, and title-based matching strategies.
"""

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from difflib import SequenceMatcher

from sqlalchemy import Integer, func
from sqlalchemy.orm import aliased
from sqlmodel import Session, select

from bookcard.models.config import Library
from bookcard.models.core import Author, Book, BookAuthorLink, BookSeriesLink, Series
from bookcard.repositories.session_manager import CalibreSessionManager
from bookcard.services.readlist.interfaces import (
    BookMatcher,
    BookMatchResult,
    BookReference,
)

logger = logging.getLogger(__name__)


def _env_flag(name: str, default: bool) -> bool:
    """Read a boolean flag from environment variables.

    Parameters
    ----------
    name : str
        Environment variable name.
    default : bool
        Default value if variable is not set or invalid.

    Returns
    -------
    bool
        Parsed boolean value.
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# Module-level configuration flags for matching behaviour.
# These can be tuned via environment variables:
# - BOOKCARD_READLIST_REQUIRE_YEAR_EXACT
# - BOOKCARD_READLIST_REQUIRE_YEAR_FUZZY
USE_YEAR_IN_EXACT_MATCH = _env_flag(
    "BOOKCARD_READLIST_REQUIRE_YEAR_EXACT",
    True,
)
USE_YEAR_IN_FUZZY_MATCH = _env_flag(
    "BOOKCARD_READLIST_REQUIRE_YEAR_FUZZY",
    True,
)


class BookMatcherService(BookMatcher):
    """Service for matching book references to library books.

    Uses multiple matching strategies:
    1. Exact match: Series name + series_index + year
    2. Fuzzy match: Series name similarity + series_index proximity
    3. Title match: Title similarity + author match
    4. No match: Returns None with confidence 0.0
    """

    def __init__(
        self,
        library: Library,
        exact_match_threshold: float = 1.0,
        fuzzy_series_similarity: float = 0.85,
        fuzzy_index_tolerance: float = 0.5,
        fuzzy_year_tolerance: int = 1,
        title_similarity_threshold: float = 0.8,
        session_manager: CalibreSessionManager | None = None,
    ) -> None:
        """Initialize book matcher service.

        Parameters
        ----------
        library : Library
            Library configuration for accessing Calibre database.
        exact_match_threshold : float
            Confidence threshold for exact matches (default: 1.0).
        fuzzy_series_similarity : float
            Minimum series name similarity for fuzzy match (default: 0.85).
        fuzzy_index_tolerance : float
            Maximum series_index difference for fuzzy match (default: 0.5).
        fuzzy_year_tolerance : int
            Maximum year difference for fuzzy match (default: 1).
        title_similarity_threshold : float
            Minimum title similarity for title match (default: 0.8).
        session_manager : CalibreSessionManager | None
            Optional session manager to use. If None, a new one is created.
        """
        self._library = library
        if session_manager:
            self._session_manager = session_manager
        else:
            self._session_manager = CalibreSessionManager(
                calibre_db_path=str(library.calibre_db_path),
                calibre_db_file=library.calibre_db_file,
            )
        self._owns_session_manager = session_manager is None
        self._exact_match_threshold = exact_match_threshold
        self._fuzzy_series_similarity = fuzzy_series_similarity
        self._fuzzy_index_tolerance = fuzzy_index_tolerance
        self._fuzzy_year_tolerance = fuzzy_year_tolerance
        self._title_similarity_threshold = title_similarity_threshold

    def close(self) -> None:
        """Close resources."""
        if self._owns_session_manager and self._session_manager:
            self._session_manager.dispose()

    @contextmanager
    def _get_session(self) -> Iterator[Session]:
        """Get a Calibre database session.

        Yields
        ------
        Session
            Calibre database session.
        """
        with self._session_manager.get_session() as session:
            yield session

    def match_books(
        self,
        references: list[BookReference],
        library_id: int,  # noqa: ARG002
    ) -> list[BookMatchResult]:
        """Match book references to library books.

        Parameters
        ----------
        references : list[BookReference]
            List of book references to match.
        library_id : int
            Library ID to search within (not used directly, but kept for interface).

        Returns
        -------
        list[BookMatchResult]
            List of match results, one per reference.
        """
        logger.info("Starting book matching for %d references", len(references))
        results: list[BookMatchResult] = []
        for ref in references:
            logger.info("Matching reference: %s", ref.model_dump())
            match_result = self._match_single_reference(ref)
            logger.info(
                "Match result for reference %s: book_id=%s, confidence=%.3f, match_type=%s",
                ref.model_dump(),
                match_result.book_id,
                match_result.confidence,
                match_result.match_type,
            )
            results.append(match_result)
        return results

    def _match_single_reference(self, ref: BookReference) -> BookMatchResult:
        """Match a single book reference.

        Parameters
        ----------
        ref : BookReference
            Book reference to match.

        Returns
        -------
        BookMatchResult
            Match result with book_id, confidence, and match_type.
        """
        # Try exact match first
        exact_match = self._try_exact_match(ref)
        if exact_match is not None:
            return BookMatchResult(
                reference=ref,
                book_id=exact_match,
                confidence=1.0,
                match_type="exact",
            )

        # Try fuzzy match
        fuzzy_match = self._try_fuzzy_match(ref)
        if fuzzy_match is not None:
            book_id, confidence = fuzzy_match
            return BookMatchResult(
                reference=ref,
                book_id=book_id,
                confidence=confidence,
                match_type="fuzzy",
            )

        # Try title match
        title_match = self._try_title_match(ref)
        if title_match is not None:
            book_id, confidence = title_match
            return BookMatchResult(
                reference=ref,
                book_id=book_id,
                confidence=confidence,
                match_type="title",
            )

        # No match found
        return BookMatchResult(
            reference=ref,
            book_id=None,
            confidence=0.0,
            match_type="none",
        )

    def _try_exact_match(self, ref: BookReference) -> int | None:
        """Try to find an exact match for the reference.

        Exact match requires:
        - Series name exact match (case-insensitive)
        - Series index matches volume/issue
        - Year matches (if both available)

        Parameters
        ----------
        ref : BookReference
            Book reference to match.

        Returns
        -------
        int | None
            Book ID if exact match found, None otherwise.
        """
        if not ref.series:
            logger.info(
                "Skipping exact match for reference without series: %s",
                ref.model_dump(),
            )
            return None

        # Prefer issue number when available; fall back to volume index.
        expected_index = ref.issue if ref.issue is not None else ref.volume

        with self._get_session() as session:
            # Build query for exact series match
            series_alias = aliased(Series)
            stmt = (
                select(Book.id, Book.series_index, Book.pubdate)
                .join(BookSeriesLink, Book.id == BookSeriesLink.book)  # type: ignore[invalid-argument-type]
                .join(series_alias, BookSeriesLink.series == series_alias.id)  # type: ignore[invalid-argument-type]
                .where(func.lower(series_alias.name) == ref.series.lower())
            )

            # Filter by series_index if available
            if expected_index is not None:
                stmt = stmt.where(Book.series_index == expected_index)

            # Filter by year if available and year matching is enabled
            if USE_YEAR_IN_EXACT_MATCH and ref.year is not None:
                # Extract year from pubdate
                stmt = stmt.where(
                    func.cast(func.strftime("%Y", Book.pubdate), Integer) == ref.year
                )

            results = list(session.exec(stmt).all())

            logger.info(
                "Exact match query for reference %s -> %d result(s), expected_index=%s, year=%s (year_matching=%s)",
                ref.model_dump(),
                len(results),
                expected_index,
                ref.year,
                USE_YEAR_IN_EXACT_MATCH,
            )

            if len(results) == 1:
                book_id, series_index, pubdate = results[0]
                logger.info(
                    "Exact match selected: book_id=%s, series_index=%s, pubdate=%s",
                    book_id,
                    series_index,
                    pubdate,
                )
                return book_id

            # If multiple results, prefer the one with matching year
            if ref.year is not None and len(results) > 1:
                for book_id, series_index, pubdate in results:
                    if pubdate and pubdate.year == ref.year:
                        logger.info(
                            "Exact match (by year) selected: book_id=%s, series_index=%s, pubdate=%s",
                            book_id,
                            series_index,
                            pubdate,
                        )
                        return book_id

            # If still multiple or none, return first or None
            if results:
                book_id, series_index, pubdate = results[0]
                logger.info(
                    "Exact match fallback selected: book_id=%s, series_index=%s, pubdate=%s",
                    book_id,
                    series_index,
                    pubdate,
                )
                return book_id

            logger.info("No exact match results for reference: %s", ref.model_dump())
            return None

    def _try_fuzzy_match(self, ref: BookReference) -> tuple[int, float] | None:
        """Try to find a fuzzy match for the reference.

        Fuzzy match requires:
        - Series name similarity > threshold
        - Series index within tolerance
        - Year within tolerance (if available)

        Parameters
        ----------
        ref : BookReference
            Book reference to match.

        Returns
        -------
        tuple[int, float] | None
            Tuple of (book_id, confidence) if fuzzy match found, None otherwise.
        """
        if not ref.series:
            return None

        # Get all books with similar series names
        all_books = self._get_all_books_with_series()
        best_match = None
        best_confidence = 0.0
        # Prefer issue index when available; fall back to volume.
        expected_index = ref.issue if ref.issue is not None else ref.volume

        for book_id, series_index, pubdate, series_name in all_books:
            if not series_name:
                continue

            confidence = self._evaluate_fuzzy_match(
                ref,
                book_id,
                series_index,
                pubdate,
                series_name,
                expected_index,
            )

            if confidence is not None and confidence > best_confidence:
                best_confidence = confidence
                best_match = book_id

        if best_match is not None:
            return (best_match, best_confidence)

        return None

    def _get_all_books_with_series(
        self,
    ) -> list[tuple[int, float, datetime | None, str | None]]:
        """Get all books with their series information.

        Returns
        -------
        list[tuple[int, float, datetime | None, str | None]]
            List of (book_id, series_index, pubdate, series_name) tuples.
        """
        with self._get_session() as session:
            series_alias = aliased(Series)
            stmt = (
                select(Book.id, Book.series_index, Book.pubdate, series_alias.name)
                .join(BookSeriesLink, Book.id == BookSeriesLink.book)  # type: ignore[invalid-argument-type]
                .join(series_alias, BookSeriesLink.series == series_alias.id)  # type: ignore[invalid-argument-type]
            )
            return list(session.exec(stmt).all())

    def _evaluate_fuzzy_match(
        self,
        ref: BookReference,
        book_id: int,  # noqa: ARG002
        series_index: float,
        pubdate: datetime | None,
        series_name: str,
        expected_index: float | None,
    ) -> float | None:
        """Evaluate if a book matches fuzzy criteria and return confidence.

        Parameters
        ----------
        ref : BookReference
            Reference to match against.
        book_id : int
            Book ID (unused, kept for consistency).
        series_index : float
            Book's series index.
        pubdate : datetime | None
            Book's publication date.
        series_name : str
            Book's series name.
        expected_index : float | None
            Expected series index.

        Returns
        -------
        float | None
            Confidence score if match passes all criteria, None otherwise.
        """
        # Calculate series name similarity
        if not ref.series:
            return None
        series_sim = self._string_similarity(
            ref.series.lower(),
            series_name.lower(),
        )

        if series_sim < self._fuzzy_series_similarity:
            return None

        # Check series_index proximity
        if expected_index is not None:
            index_diff = abs(series_index - expected_index)
            if index_diff > self._fuzzy_index_tolerance:
                return None

        # Check year proximity (optional)
        if USE_YEAR_IN_FUZZY_MATCH and ref.year is not None and pubdate:
            year_diff = abs(pubdate.year - ref.year)
            if year_diff > self._fuzzy_year_tolerance:
                return None

        # Calculate confidence
        return self._calculate_fuzzy_confidence(
            series_sim,
            series_index,
            expected_index,
            pubdate,
            ref.year,
        )

    def _try_title_match(self, ref: BookReference) -> tuple[int, float] | None:
        """Try to find a match based on title and author.

        Title match requires:
        - Title similarity > threshold
        - Author match (if both available)

        Parameters
        ----------
        ref : BookReference
            Book reference to match.

        Returns
        -------
        tuple[int, float] | None
            Tuple of (book_id, confidence) if title match found, None otherwise.
        """
        if not ref.title:
            return None

        with self._get_session() as session:
            # Build query for title search
            author_alias = aliased(Author)
            stmt = (
                select(Book.id, Book.title, author_alias.name)
                .outerjoin(BookAuthorLink, Book.id == BookAuthorLink.book)  # type: ignore[invalid-argument-type]
                .outerjoin(author_alias, BookAuthorLink.author == author_alias.id)  # type: ignore[invalid-argument-type]
                .distinct()
            )

            all_books = list(session.exec(stmt).all())

            best_match = None
            best_confidence = 0.0

            for book_id, title, author_name in all_books:
                if not title:
                    continue

                # Calculate title similarity
                title_sim = self._string_similarity(
                    ref.title.lower(),
                    title.lower(),
                )

                if title_sim < self._title_similarity_threshold:
                    continue

                # Check author match if both available
                if ref.author and author_name:
                    author_sim = self._string_similarity(
                        ref.author.lower(),
                        author_name.lower(),
                    )
                    if author_sim < 0.7:  # Require reasonable author match
                        continue
                    # Boost confidence if author matches well
                    if author_sim > 0.9:
                        title_sim = min(1.0, title_sim + 0.1)

                # Calculate confidence (0.5-0.7 range for title matches)
                confidence = 0.5 + (title_sim - self._title_similarity_threshold) * 0.4
                confidence = max(0.5, min(0.7, confidence))

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = book_id

            if best_match is not None:
                return (best_match, best_confidence)

            return None

    def _calculate_fuzzy_confidence(
        self,
        series_sim: float,
        series_index: float,
        expected_index: float | None,
        pubdate: datetime | None,
        ref_year: int | None,
    ) -> float:
        """Calculate confidence score for fuzzy match.

        Parameters
        ----------
        series_sim : float
            Series name similarity score.
        series_index : float
            Book's series index.
        expected_index : float | None
            Expected series index from reference.
        pubdate : datetime | None
            Book's publication date.
        ref_year : int | None
            Expected year from reference.

        Returns
        -------
        float
            Confidence score clamped to 0.7-0.9 range.
        """
        confidence = series_sim
        if expected_index is not None:
            # Reduce confidence based on index difference
            index_penalty = min(
                abs(series_index - expected_index) / self._fuzzy_index_tolerance,
                0.2,
            )
            confidence -= index_penalty * 0.1

        if ref_year is not None and pubdate:
            # Reduce confidence based on year difference
            year_penalty = min(
                abs(pubdate.year - ref_year) / self._fuzzy_year_tolerance,
                0.1,
            )
            confidence -= year_penalty * 0.1

        return max(0.7, min(0.9, confidence))  # Clamp to 0.7-0.9

    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings.

        Parameters
        ----------
        str1 : str
            First string.
        str2 : str
            Second string.

        Returns
        -------
        float
            Similarity score (0.0-1.0).
        """
        return SequenceMatcher(None, str1, str2).ratio()
