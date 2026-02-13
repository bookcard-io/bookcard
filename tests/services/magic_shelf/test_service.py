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

from unittest.mock import MagicMock

import pytest

from bookcard.models.shelves import Shelf, ShelfTypeEnum
from bookcard.services.magic_shelf.service import MagicShelfService


class TestMagicShelfService:
    @pytest.fixture
    def mock_shelf_repo(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_book_repo(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_evaluator(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def service(
        self,
        mock_shelf_repo: MagicMock,
        mock_book_repo: MagicMock,
        mock_evaluator: MagicMock,
    ) -> MagicShelfService:
        return MagicShelfService(mock_shelf_repo, {1: mock_book_repo}, mock_evaluator)

    def test_get_books_shelf_not_found(
        self,
        service: MagicShelfService,
        mock_shelf_repo: MagicMock,
    ) -> None:
        """Test error when shelf does not exist."""
        mock_shelf_repo.get.return_value = None
        with pytest.raises(ValueError, match="Shelf 1 not found"):
            service.get_books_for_shelf(1)

    def test_count_books_shelf_not_found(
        self,
        service: MagicShelfService,
        mock_shelf_repo: MagicMock,
    ) -> None:
        """Test count error when shelf does not exist."""
        mock_shelf_repo.get.return_value = None
        with pytest.raises(ValueError, match="Shelf 1 not found"):
            service.count_books_for_shelf(1)

    def test_get_books_not_magic_shelf(
        self,
        service: MagicShelfService,
        mock_shelf_repo: MagicMock,
    ) -> None:
        """Test error when shelf is not a magic shelf."""
        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.SHELF
        mock_shelf_repo.get.return_value = shelf
        with pytest.raises(ValueError, match="Shelf 1 is not a Magic Shelf"):
            service.get_books_for_shelf(1)

    def test_count_books_not_magic_shelf(
        self,
        service: MagicShelfService,
        mock_shelf_repo: MagicMock,
    ) -> None:
        """Test count error when shelf is not a magic shelf."""
        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.SHELF
        mock_shelf_repo.get.return_value = shelf
        with pytest.raises(ValueError, match="Shelf 1 is not a Magic Shelf"):
            service.count_books_for_shelf(1)

    def test_get_books_success(
        self,
        service: MagicShelfService,
        mock_shelf_repo: MagicMock,
        mock_book_repo: MagicMock,
        mock_evaluator: MagicMock,
    ) -> None:
        """Test successful retrieval of books."""
        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.MAGIC_SHELF
        shelf.filter_rules = {"rules": []}  # Valid empty rules
        mock_shelf_repo.get.return_value = shelf

        mock_evaluator.build_matching_book_ids_stmt.return_value = "ids_query"
        mock_book = MagicMock()
        mock_book.book.sort = "Book Title"
        mock_book.book.title = "Book Title"
        mock_book.book.timestamp = "2025-01-01"
        mock_book_repo.list_books_by_ids_query.return_value = [mock_book]
        mock_book_repo.count_books_by_ids_query.return_value = 1

        books, count = service.get_books_for_shelf(1)

        assert len(books) == 1
        assert count == 1
        mock_book_repo.list_books_by_ids_query.assert_called_once()
        call_args = mock_book_repo.list_books_by_ids_query.call_args
        assert call_args[0][0] == "ids_query"
        call_kwargs = call_args[1]
        assert call_kwargs["offset"] == 0

    def test_count_books_success(
        self,
        service: MagicShelfService,
        mock_shelf_repo: MagicMock,
        mock_book_repo: MagicMock,
        mock_evaluator: MagicMock,
    ) -> None:
        """Test successful counting of books."""
        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.MAGIC_SHELF
        shelf.filter_rules = {"rules": []}  # Valid empty rules
        mock_shelf_repo.get.return_value = shelf

        mock_evaluator.build_matching_book_ids_stmt.return_value = "ids_query"
        mock_book_repo.count_books_by_ids_query.return_value = 7

        count = service.count_books_for_shelf(1)

        assert count == 7
        mock_book_repo.count_books_by_ids_query.assert_called_once_with("ids_query")

    def test_get_books_pagination(
        self,
        service: MagicShelfService,
        mock_shelf_repo: MagicMock,
        mock_book_repo: MagicMock,
    ) -> None:
        """Test pagination is applied after merging results from all libraries."""
        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.MAGIC_SHELF
        shelf.filter_rules = {"rules": []}
        mock_shelf_repo.get.return_value = shelf

        # Create 15 mock books
        mock_books = []
        for i in range(15):
            mb = MagicMock()
            mb.book.sort = f"Book {i:02d}"
            mb.book.title = f"Book {i:02d}"
            mb.book.timestamp = f"2025-01-{i + 1:02d}"
            mb.book.id = i + 1
            mock_books.append(mb)

        mock_book_repo.count_books_by_ids_query.return_value = 15
        mock_book_repo.list_books_by_ids_query.return_value = mock_books

        books, count = service.get_books_for_shelf(1, page=2, page_size=10)

        assert count == 15
        # Page 2 with page_size 10 gives items 10-14 (5 items)
        assert len(books) == 5

    def test_invalid_rules_returns_empty(
        self,
        service: MagicShelfService,
        mock_shelf_repo: MagicMock,
        mock_book_repo: MagicMock,
    ) -> None:
        """Test that invalid rules result in empty return without error."""
        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.MAGIC_SHELF
        shelf.filter_rules = {"invalid": "data", "rules": "not_a_list"}
        mock_shelf_repo.get.return_value = shelf

        books, count = service.get_books_for_shelf(1)

        assert books == []
        assert count == 0
        mock_book_repo.list_books_by_ids_query.assert_not_called()

    def test_count_books_invalid_rules_returns_zero(
        self,
        service: MagicShelfService,
        mock_shelf_repo: MagicMock,
        mock_book_repo: MagicMock,
    ) -> None:
        """Test that invalid rules result in zero without error."""
        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.MAGIC_SHELF
        shelf.filter_rules = {"invalid": "data", "rules": "not_a_list"}
        mock_shelf_repo.get.return_value = shelf

        count = service.count_books_for_shelf(1)

        assert count == 0
        mock_book_repo.count_books_by_ids_query.assert_not_called()

    def test_empty_rules_returns_empty_group(
        self,
        service: MagicShelfService,
        mock_shelf_repo: MagicMock,
        mock_book_repo: MagicMock,
        mock_evaluator: MagicMock,
    ) -> None:
        """Test that None rules result in empty group rule."""
        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.MAGIC_SHELF
        shelf.filter_rules = None
        mock_shelf_repo.get.return_value = shelf

        service.get_books_for_shelf(1)

        # Should call evaluator with empty GroupRule
        mock_evaluator.build_matching_book_ids_stmt.assert_called_once()
        args = mock_evaluator.build_matching_book_ids_stmt.call_args[0]
        assert args[0].rules == []


class TestMagicShelfServiceMultiLibrary:
    """Tests for multi-library magic shelf query merging."""

    @pytest.fixture
    def mock_shelf_repo(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_evaluator(self) -> MagicMock:
        return MagicMock()

    def _make_book(
        self,
        book_id: int,
        title: str,
        timestamp: str = "2025-01-01",
    ) -> MagicMock:
        """Create a mock BookWithRelations."""
        book = MagicMock()
        book.book.id = book_id
        book.book.title = title
        book.book.sort = title
        book.book.timestamp = timestamp
        return book

    def test_count_sums_across_libraries(
        self,
        mock_shelf_repo: MagicMock,
        mock_evaluator: MagicMock,
    ) -> None:
        """Test count_books_for_shelf sums counts across libraries."""
        repo_a = MagicMock()
        repo_a.count_books_by_ids_query.return_value = 3
        repo_b = MagicMock()
        repo_b.count_books_by_ids_query.return_value = 5

        service = MagicShelfService(
            mock_shelf_repo, {1: repo_a, 2: repo_b}, mock_evaluator
        )

        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.MAGIC_SHELF
        shelf.filter_rules = {"rules": []}
        mock_shelf_repo.get.return_value = shelf

        mock_evaluator.build_matching_book_ids_stmt.return_value = "ids_query"

        count = service.count_books_for_shelf(1)
        assert count == 8
        repo_a.count_books_by_ids_query.assert_called_once_with("ids_query")
        repo_b.count_books_by_ids_query.assert_called_once_with("ids_query")

    def test_get_books_merges_and_tags_library_id(
        self,
        mock_shelf_repo: MagicMock,
        mock_evaluator: MagicMock,
    ) -> None:
        """Test get_books_for_shelf merges books and tags with library_id."""
        book_a = self._make_book(1, "Alpha", "2025-01-03")
        book_b = self._make_book(2, "Beta", "2025-01-01")
        book_c = self._make_book(3, "Gamma", "2025-01-02")

        repo_a = MagicMock()
        repo_a.count_books_by_ids_query.return_value = 1
        repo_a.list_books_by_ids_query.return_value = [book_a]

        repo_b = MagicMock()
        repo_b.count_books_by_ids_query.return_value = 2
        repo_b.list_books_by_ids_query.return_value = [book_b, book_c]

        service = MagicShelfService(
            mock_shelf_repo,
            {10: repo_a, 20: repo_b},
            mock_evaluator,
        )

        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.MAGIC_SHELF
        shelf.filter_rules = {"rules": []}
        mock_shelf_repo.get.return_value = shelf

        mock_evaluator.build_matching_book_ids_stmt.return_value = "ids_query"

        books, total = service.get_books_for_shelf(
            1, sort_by="timestamp", sort_order="desc"
        )

        assert total == 3
        assert len(books) == 3
        # Verify library_id tagging
        assert book_a.library_id == 10
        assert book_b.library_id == 20
        assert book_c.library_id == 20
        # Verify desc sort by timestamp: "2025-01-03", "2025-01-02", "2025-01-01"
        assert books[0] is book_a
        assert books[1] is book_c
        assert books[2] is book_b

    def test_get_books_paginates_after_merge(
        self,
        mock_shelf_repo: MagicMock,
        mock_evaluator: MagicMock,
    ) -> None:
        """Test pagination is applied after merging across libraries."""
        books_a = [
            self._make_book(i, f"A{i}", f"2025-01-{20 - i:02d}") for i in range(5)
        ]
        books_b = [
            self._make_book(i, f"B{i}", f"2025-01-{15 - i:02d}") for i in range(5)
        ]

        repo_a = MagicMock()
        repo_a.count_books_by_ids_query.return_value = 5
        repo_a.list_books_by_ids_query.return_value = books_a

        repo_b = MagicMock()
        repo_b.count_books_by_ids_query.return_value = 5
        repo_b.list_books_by_ids_query.return_value = books_b

        service = MagicShelfService(
            mock_shelf_repo,
            {1: repo_a, 2: repo_b},
            mock_evaluator,
        )

        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.MAGIC_SHELF
        shelf.filter_rules = {"rules": []}
        mock_shelf_repo.get.return_value = shelf

        mock_evaluator.build_matching_book_ids_stmt.return_value = "q"

        books, total = service.get_books_for_shelf(
            1,
            page=2,
            page_size=4,
            sort_by="timestamp",
            sort_order="desc",
        )

        assert total == 10
        # Page 2, size 4 → items 4..7
        assert len(books) == 4

    def test_from_single_repo_factory(
        self,
        mock_shelf_repo: MagicMock,
        mock_evaluator: MagicMock,
    ) -> None:
        """Test from_single_repo creates service with single-library dict."""
        repo = MagicMock()
        service = MagicShelfService.from_single_repo(
            mock_shelf_repo,
            repo,
            mock_evaluator,
            library_id=42,
        )
        assert service._book_repos == {42: repo}
