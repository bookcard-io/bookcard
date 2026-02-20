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

"""Multi-library book query service.

Queries books across multiple Calibre libraries, merges results, and
provides sorted, paginated responses.  Follows the same cross-library
aggregation pattern as :class:`MagicShelfService`.
"""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

from bookcard.repositories.calibre.repository import CalibreBookRepository

if TYPE_CHECKING:
    from collections.abc import Callable

    from bookcard.models.config import Library
    from bookcard.repositories.models import BookWithFullRelations, BookWithRelations

logger = logging.getLogger(__name__)


class MultiLibraryBookService:
    """Query and merge books from multiple Calibre libraries.

    Parameters
    ----------
    libraries : dict[int, Library]
        Mapping of ``library_id`` to :class:`Library` configuration.
    """

    def __init__(self, libraries: dict[int, Library]) -> None:
        self._libraries = libraries
        self._repos: dict[int, CalibreBookRepository] = {
            lib_id: CalibreBookRepository(
                calibre_db_path=lib.calibre_db_path,
                calibre_db_file=lib.calibre_db_file,
            )
            for lib_id, lib in libraries.items()
        }

    def list_books(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search_query: str | None = None,
        author_id: int | None = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        full: bool = False,
        pubdate_month: int | None = None,
        pubdate_day: int | None = None,
    ) -> tuple[list[BookWithRelations | BookWithFullRelations], int]:
        """List books across all configured libraries.

        Each library is queried independently with the same filters.  Results
        are tagged with ``library_id``, merged, sorted, and paginated.

        Parameters
        ----------
        page : int
            Page number (1-indexed).
        page_size : int
            Items per page.
        search_query : str | None
            Optional title/author search.
        author_id : int | None
            Optional Calibre author ID filter.
        sort_by : str
            Sort field (``timestamp``, ``pubdate``, ``title``,
            ``author_sort``, ``series_index``, ``random``).
        sort_order : str
            ``'asc'`` or ``'desc'``.
        full : bool
            Return full book metadata.
        pubdate_month : int | None
            Optional publication-date month filter.
        pubdate_day : int | None
            Optional publication-date day filter.

        Returns
        -------
        tuple[list[BookWithRelations | BookWithFullRelations], int]
            ``(paginated_books, total_count)``
        """
        all_books: list[BookWithRelations | BookWithFullRelations] = []
        total_count = 0
        fetch_limit = page * page_size

        for lib_id, repo in self._repos.items():
            count = repo.count_books(
                search_query=search_query,
                author_id=author_id,
                pubdate_month=pubdate_month,
                pubdate_day=pubdate_day,
            )
            total_count += count
            if count == 0:
                continue

            books = repo.list_books(
                limit=min(count, fetch_limit),
                offset=0,
                search_query=search_query,
                author_id=author_id,
                sort_by=sort_by,
                sort_order=sort_order,
                full=full,
                pubdate_month=pubdate_month,
                pubdate_day=pubdate_day,
            )
            for book in books:
                book.library_id = lib_id
            all_books.extend(books)

        if sort_by == "random":
            random.shuffle(all_books)
        else:
            all_books.sort(
                key=_get_sort_key(sort_by),
                reverse=(sort_order == "desc"),
            )

        offset = (page - 1) * page_size
        return all_books[offset : offset + page_size], total_count

    def list_books_with_filters(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        author_ids: list[int] | None = None,
        title_ids: list[int] | None = None,
        genre_ids: list[int] | None = None,
        publisher_ids: list[int] | None = None,
        identifier_ids: list[int] | None = None,
        series_ids: list[int] | None = None,
        formats: list[str] | None = None,
        rating_ids: list[int] | None = None,
        language_ids: list[int] | None = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        full: bool = False,
    ) -> tuple[list[BookWithRelations | BookWithFullRelations], int]:
        """List books across libraries using multi-filter criteria.

        Parameters
        ----------
        page : int
            Page number (1-indexed).
        page_size : int
            Items per page.
        author_ids : list[int] | None
            Author IDs (OR).
        title_ids : list[int] | None
            Book IDs (OR).
        genre_ids : list[int] | None
            Tag IDs (OR).
        publisher_ids : list[int] | None
            Publisher IDs (OR).
        identifier_ids : list[int] | None
            Identifier IDs (OR).
        series_ids : list[int] | None
            Series IDs (OR).
        formats : list[str] | None
            Format strings (OR).
        rating_ids : list[int] | None
            Rating IDs (OR).
        language_ids : list[int] | None
            Language IDs (OR).
        sort_by : str
            Sort field.
        sort_order : str
            ``'asc'`` or ``'desc'``.
        full : bool
            Return full book metadata.

        Returns
        -------
        tuple[list[BookWithRelations | BookWithFullRelations], int]
            ``(paginated_books, total_count)``
        """
        all_books: list[BookWithRelations | BookWithFullRelations] = []
        total_count = 0
        fetch_limit = page * page_size

        for lib_id, repo in self._repos.items():
            count = repo.count_books_with_filters(
                author_ids=author_ids,
                title_ids=title_ids,
                genre_ids=genre_ids,
                publisher_ids=publisher_ids,
                identifier_ids=identifier_ids,
                series_ids=series_ids,
                formats=formats,
                rating_ids=rating_ids,
                language_ids=language_ids,
            )
            total_count += count
            if count == 0:
                continue

            books = repo.list_books_with_filters(
                limit=min(count, fetch_limit),
                offset=0,
                author_ids=author_ids,
                title_ids=title_ids,
                genre_ids=genre_ids,
                publisher_ids=publisher_ids,
                identifier_ids=identifier_ids,
                series_ids=series_ids,
                formats=formats,
                rating_ids=rating_ids,
                language_ids=language_ids,
                sort_by=sort_by,
                sort_order=sort_order,
                full=full,
            )
            for book in books:
                book.library_id = lib_id
            all_books.extend(books)

        all_books.sort(
            key=_get_sort_key(sort_by),
            reverse=(sort_order == "desc"),
        )

        offset = (page - 1) * page_size
        return all_books[offset : offset + page_size], total_count


def _get_sort_key(
    sort_by: str,
) -> Callable:
    """Return a sort-key function for cross-library result merging.

    Parameters
    ----------
    sort_by : str
        Sort field name.

    Returns
    -------
    callable
        Key function suitable for :func:`list.sort`.
    """

    def _key(b: BookWithRelations | BookWithFullRelations) -> str | float:
        if sort_by == "title":
            return (b.book.sort or b.book.title or "").lower()
        if sort_by == "author_sort":
            return (b.book.author_sort or "").lower()
        if sort_by == "pubdate":
            return str(b.book.pubdate or "")
        if sort_by == "series_index":
            return b.book.series_index or 0.0
        return str(b.book.timestamp or "")

    return _key
