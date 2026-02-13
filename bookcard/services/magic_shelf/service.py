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

"""Magic Shelf service.

This module orchestrates the retrieval of books for Magic Shelves.
It adheres to DIP by depending on abstractions (repositories) and SRP
by delegating rule evaluation to a dedicated component.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from bookcard.models.magic_shelf_rules import GroupRule
from bookcard.models.shelves import ShelfTypeEnum

if TYPE_CHECKING:
    from collections.abc import Callable

    from bookcard.repositories.interfaces import IBookRepository
    from bookcard.repositories.models import BookWithFullRelations, BookWithRelations
    from bookcard.repositories.shelf_repository import ShelfRepository
    from bookcard.services.magic_shelf.evaluator import BookRuleEvaluator

logger = logging.getLogger(__name__)


class MagicShelfService:
    """Service for retrieving books for Magic Shelves.

    Supports querying books across multiple libraries by holding a mapping
    of ``library_id`` to ``IBookRepository``.  When only a single library is
    configured the behaviour is identical to the original single-repo design.
    """

    def __init__(
        self,
        shelf_repo: ShelfRepository,
        book_repos: dict[int, IBookRepository],
        evaluator: BookRuleEvaluator,
    ) -> None:
        self._shelf_repo = shelf_repo
        self._book_repos = book_repos
        self._evaluator = evaluator

    # ------------------------------------------------------------------
    # Legacy single-repo constructor for backward compatibility
    # ------------------------------------------------------------------
    @classmethod
    def from_single_repo(
        cls,
        shelf_repo: ShelfRepository,
        book_repo: IBookRepository,
        evaluator: BookRuleEvaluator,
        library_id: int,
    ) -> MagicShelfService:
        """Create an instance backed by a single library repo.

        Parameters
        ----------
        shelf_repo : ShelfRepository
            Shelf repository.
        book_repo : IBookRepository
            Single-library book repository.
        evaluator : BookRuleEvaluator
            Rule evaluator.
        library_id : int
            Library ID for the repo.

        Returns
        -------
        MagicShelfService
            Service instance scoped to one library.
        """
        return cls(shelf_repo, {library_id: book_repo}, evaluator)

    def count_books_for_shelf(self, shelf_id: int) -> int:
        """Count books matching the rules of a Magic Shelf.

        Parameters
        ----------
        shelf_id : int
            ID of the shelf.

        Returns
        -------
        int
            Total number of books matching the shelf rules.

        Raises
        ------
        ValueError
            If shelf not found or not a magic shelf.
        """
        shelf = self._shelf_repo.get(shelf_id)
        if not shelf:
            msg = f"Shelf {shelf_id} not found"
            raise ValueError(msg)

        if shelf.shelf_type != ShelfTypeEnum.MAGIC_SHELF:
            msg = f"Shelf {shelf_id} is not a Magic Shelf"
            raise ValueError(msg)

        group_rule = self._parse_rules(shelf.filter_rules, shelf_id)
        if not group_rule:
            return 0

        book_ids_query = self._evaluator.build_matching_book_ids_stmt(group_rule)
        total = 0
        for repo in self._book_repos.values():
            total += repo.count_books_by_ids_query(book_ids_query)
        return total

    def get_books_for_shelf(
        self,
        shelf_id: int,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        full: bool = False,
    ) -> tuple[list[BookWithRelations | BookWithFullRelations], int]:
        """Get books matching the rules of a Magic Shelf.

        Queries each library's Calibre DB independently then merges the
        results.  Pagination is applied after merging so page boundaries
        are consistent.

        Parameters
        ----------
        shelf_id : int
            ID of the shelf.
        page : int
            Page number (1-based).
        page_size : int
            Number of items per page.
        sort_by : str
            Field to sort by.
        sort_order : str
            Sort order ('asc' or 'desc').
        full : bool
            Whether to return full book details.

        Returns
        -------
        tuple[list[BookWithRelations | BookWithFullRelations], int]
            Tuple of (books, total_count).

        Raises
        ------
        ValueError
            If shelf not found or not a magic shelf.
        """
        shelf = self._shelf_repo.get(shelf_id)
        if not shelf:
            msg = f"Shelf {shelf_id} not found"
            raise ValueError(msg)

        if shelf.shelf_type != ShelfTypeEnum.MAGIC_SHELF:
            msg = f"Shelf {shelf_id} is not a Magic Shelf"
            raise ValueError(msg)

        group_rule = self._parse_rules(shelf.filter_rules, shelf_id)
        if not group_rule:
            return [], 0

        book_ids_query = self._evaluator.build_matching_book_ids_stmt(group_rule)

        # Collect books from all libraries
        all_books: list[BookWithRelations | BookWithFullRelations] = []
        total_count = 0
        for library_id, repo in self._book_repos.items():
            count = repo.count_books_by_ids_query(book_ids_query)
            total_count += count
            # Fetch all matched books (we paginate after merge)
            books = repo.list_books_by_ids_query(
                book_ids_query,
                limit=count or 1,
                offset=0,
                sort_by=sort_by,
                sort_order=sort_order,
                full=full,
            )
            # Tag each book with its library_id
            for book in books:
                book.library_id = library_id
            all_books.extend(books)

        # Sort merged results
        reverse = sort_order == "desc"
        sort_key = self._get_sort_key(sort_by)
        all_books.sort(key=sort_key, reverse=reverse)

        # Paginate
        offset = (page - 1) * page_size
        paginated = all_books[offset : offset + page_size]

        return paginated, total_count

    @staticmethod
    def _get_sort_key(
        sort_by: str,
    ) -> Callable[[BookWithRelations | BookWithFullRelations], str | int]:
        """Return a sort key function for the given field name.

        Parameters
        ----------
        sort_by : str
            Field to sort by (``timestamp``, ``title``, ``id``).

        Returns
        -------
        Callable
            Callable suitable for ``list.sort(key=...)``.
        """

        def _key(b: BookWithRelations | BookWithFullRelations) -> str | int:
            if sort_by == "title":
                return (b.book.sort or b.book.title or "").lower()
            if sort_by == "id":
                return b.book.id or 0
            # Default to timestamp
            return str(b.book.timestamp or "")

        return _key

    def _parse_rules(
        self,
        rules_data: dict[str, Any] | None,
        shelf_id: int,
    ) -> GroupRule | None:
        """Parse and validate filter rules.

        Parameters
        ----------
        rules_data : dict[str, Any] | None
            Raw rules data from the shelf.
        shelf_id : int
            ID of the shelf (for logging).

        Returns
        -------
        GroupRule | None
            Parsed GroupRule, or None if rules are invalid or empty.
        """
        if not rules_data:
            # Let's assume unconfigured shelf = no books.
            return GroupRule()

        try:
            return GroupRule.model_validate(rules_data)
        except Exception:
            logger.exception("Failed to parse filter rules for shelf %d", shelf_id)
            return None
