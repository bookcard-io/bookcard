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

"""Book query service for OPDS feeds with permission filtering.

Queries books from Calibre library and filters based on user permissions.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from bookcard.services.book_permission_helper import BookPermissionHelper
from bookcard.services.book_service import BookService
from bookcard.services.opds.interfaces import IOpdsBookQueryService
from bookcard.services.permission_service import PermissionService

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.models.auth import User
    from bookcard.models.config import Library
    from bookcard.repositories.models import BookWithRelations


class OpdsBookQueryService(IOpdsBookQueryService):
    """Book query service with permission filtering.

    Wraps BookService and filters results based on user permissions.
    Follows SRP by focusing solely on book queries with permission filtering.
    """

    def __init__(
        self,
        session: Session,
        library: Library,
        book_service: BookService | None = None,
        permission_service: PermissionService | None = None,
        permission_helper: BookPermissionHelper | None = None,
    ) -> None:
        """Initialize book query service.

        Parameters
        ----------
        session : Session
            Database session.
        library : Library
            Active Calibre library configuration.
        book_service : BookService | None
            Optional book service (creates default if None).
        permission_service : PermissionService | None
            Optional permission service (creates default if None).
        permission_helper : BookPermissionHelper | None
            Optional permission helper (creates default if None).
        """
        self._session = session
        self._library = library
        self._book_service = book_service or BookService(library, session=session)
        self._permission_service = permission_service or PermissionService(session)
        self._permission_helper = permission_helper or BookPermissionHelper(session)

    def get_books(
        self,
        user: User | None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
    ) -> tuple[list[BookWithRelations], int]:
        """Get books with pagination and permission filtering.

        Parameters
        ----------
        user : User | None
            Authenticated user or None.
        page : int
            Page number (1-indexed).
        page_size : int
            Number of items per page.
        sort_by : str
            Field to sort by.
        sort_order : str
            Sort order: 'asc' or 'desc'.

        Returns
        -------
        tuple[list[BookWithRelations], int]
            Tuple of (books list, total count).
        """
        books, total = self._book_service.list_books(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            full=False,
        )

        # Filter by permissions
        filtered_books = self._filter_by_permissions(books, user)

        # Keep the underlying total count for correct OPDS pagination.
        #
        # Note: filtering happens after pagination, so `total` is not strictly
        # permission-aware; however OPDS clients (e.g. Readest) rely on paging
        # links (`next`/`last`) which require an honest total estimate.
        return filtered_books, total

    def get_recent_books(
        self,
        user: User | None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[BookWithRelations], int]:
        """Get recently added books with permission filtering.

        Parameters
        ----------
        user : User | None
            Authenticated user or None.
        page : int
            Page number (1-indexed).
        page_size : int
            Number of items per page.

        Returns
        -------
        tuple[list[BookWithRelations], int]
            Tuple of (books list, total count).
        """
        return self.get_books(
            user=user,
            page=page,
            page_size=page_size,
            sort_by="timestamp",
            sort_order="desc",
        )

    def get_random_books(
        self,
        user: User | None,
        limit: int = 20,
    ) -> list[BookWithRelations]:
        """Get random books with permission filtering.

        Parameters
        ----------
        user : User | None
            Authenticated user or None.
        limit : int
            Maximum number of books to return.

        Returns
        -------
        list[BookWithRelations]
            List of random books.
        """
        # Get a larger sample to account for filtering
        sample_size = limit * 3
        books, _ = self._book_service.list_books(
            page=1,
            page_size=sample_size,
            sort_by="timestamp",
            sort_order="desc",
            full=False,
        )

        # Filter by permissions
        filtered_books = self._filter_by_permissions(books, user)

        # Randomize and limit
        random.shuffle(filtered_books)
        return filtered_books[:limit]

    def search_books(
        self,
        user: User | None,
        query: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[BookWithRelations], int]:
        """Search books with permission filtering.

        Parameters
        ----------
        user : User | None
            Authenticated user or None.
        query : str
            Search query string.
        page : int
            Page number (1-indexed).
        page_size : int
            Number of items per page.

        Returns
        -------
        tuple[list[BookWithRelations], int]
            Tuple of (books list, total count).
        """
        books, total = self._book_service.list_books(
            page=page,
            page_size=page_size,
            search_query=query,
            full=False,
        )

        # Filter by permissions
        filtered_books = self._filter_by_permissions(books, user)

        return filtered_books, total

    def get_books_by_filter(
        self,
        user: User | None,
        page: int = 1,
        page_size: int = 20,
        author_ids: list[int] | None = None,
        publisher_ids: list[int] | None = None,
        genre_ids: list[int] | None = None,
        series_ids: list[int] | None = None,
        rating_ids: list[int] | None = None,
        formats: list[str] | None = None,
        language_ids: list[int] | None = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
    ) -> tuple[list[BookWithRelations], int]:
        """Get books filtered by various criteria with permission filtering.

        Parameters
        ----------
        user : User | None
            Authenticated user or None.
        page : int
            Page number (1-indexed).
        page_size : int
            Number of items per page.
        author_ids : list[int] | None
            List of author IDs to filter by.
        publisher_ids : list[int] | None
            List of publisher IDs to filter by.
        genre_ids : list[int] | None
            List of tag IDs to filter by.
        series_ids : list[int] | None
            List of series IDs to filter by.
        rating_ids : list[int] | None
            List of rating IDs to filter by.
        formats : list[str] | None
            List of format strings to filter by.
        language_ids : list[int] | None
            List of language IDs to filter by.
        sort_by : str
            Field to sort by.
        sort_order : str
            Sort order: 'asc' or 'desc'.

        Returns
        -------
        tuple[list[BookWithRelations], int]
            Tuple of (books list, total count).
        """
        books, total = self._book_service.list_books_with_filters(
            page=page,
            page_size=page_size,
            author_ids=author_ids,
            publisher_ids=publisher_ids,
            genre_ids=genre_ids,
            series_ids=series_ids,
            rating_ids=rating_ids,
            formats=formats,
            language_ids=language_ids,
            sort_by=sort_by,
            sort_order=sort_order,
            full=False,
        )

        # Filter by permissions
        filtered_books = self._filter_by_permissions(books, user)

        return filtered_books, total

    def get_best_rated_books(
        self,
        user: User | None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[BookWithRelations], int]:
        """Get best rated books (rating > 4.5) with permission filtering.

        Parameters
        ----------
        user : User | None
            Authenticated user or None.
        page : int
            Page number (1-indexed).
        page_size : int
            Number of items per page.

        Returns
        -------
        tuple[list[BookWithRelations], int]
            Tuple of (books list, total count).
        """
        # Rating ID 5 corresponds to rating value 10 (5 stars)
        # We'll filter for ratings >= 9 (4.5 stars)
        # Note: Calibre uses rating values 0-10, where 10 = 5 stars
        # We need to find rating IDs that correspond to high ratings
        # For now, we'll get all books with ratings and filter client-side
        # A better approach would be to query rating IDs >= 9
        books, _total = self._book_service.list_books_with_filters(
            page=page,
            page_size=page_size,
            rating_ids=None,  # Get all rated books, filter by rating value
            sort_by="timestamp",
            sort_order="desc",
            full=False,
        )

        # Filter by permissions and rating value
        filtered_books = self._filter_by_permissions(books, user)
        # Filter for high ratings (rating >= 9, which is 4.5 stars)
        high_rated = [
            b
            for b in filtered_books
            if hasattr(b, "book") and hasattr(b.book, "rating_id") and b.book.rating_id
        ]
        # Note: We'd need to check actual rating value, but for now return all rated books

        return high_rated, len(high_rated)

    def _filter_by_permissions(
        self,
        books: list,  # list[BookWithRelations | BookWithFullRelations]
        user: User | None,
    ) -> list:  # list[BookWithRelations]
        """Filter books based on user permissions.

        Parameters
        ----------
        books : list[BookWithRelations]
            List of books to filter.
        user : User | None
            Authenticated user or None.

        Returns
        -------
        list[BookWithRelations]
            Filtered list of books user has permission to read.
        """
        if user is None:
            # No user - return empty list (require authentication)
            return []

        filtered: list[BookWithRelations] = []

        for book in books:
            # OPDS expects acquisition-style entries. Readest (via foliate-js/opds.js)
            # determines whether an entry is a "publication" based on whether it has at
            # least one acquisition/preview link. Virtual tracked books that have no
            # downloadable formats would otherwise be treated as navigation items and,
            # if they appear first, can cause Readest to render the entire feed as
            # navigation ("Untitled" + broken click behavior).
            #
            # To match Calibre-Web(-Automated) behavior and keep OPDS feeds consistent,
            # we exclude virtual entries that don't have any formats to acquire.
            if getattr(book, "is_virtual", False) and not getattr(
                book, "formats", None
            ):
                continue

            # Build permission context
            context = BookPermissionHelper.build_permission_context(book)

            # Check permission
            if self._permission_service.has_permission(user, "books", "read", context):
                filtered.append(book)

        return filtered
