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
        shelf.library_id = 1
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
        shelf.library_id = 1
        mock_shelf_repo.get.return_value = shelf
        with pytest.raises(ValueError, match="Shelf 1 is not a Magic Shelf"):
            service.count_books_for_shelf(1)

    def test_get_books_library_not_configured(
        self,
        mock_shelf_repo: MagicMock,
        mock_evaluator: MagicMock,
    ) -> None:
        """Test error when shelf's library has no configured repo."""
        service = MagicShelfService(mock_shelf_repo, {1: MagicMock()}, mock_evaluator)
        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.MAGIC_SHELF
        shelf.library_id = 999
        mock_shelf_repo.get.return_value = shelf
        with pytest.raises(ValueError, match="No book repository configured"):
            service.get_books_for_shelf(1)

    def test_get_books_success(
        self,
        service: MagicShelfService,
        mock_shelf_repo: MagicMock,
        mock_book_repo: MagicMock,
        mock_evaluator: MagicMock,
    ) -> None:
        """Test successful retrieval of books from the shelf's library."""
        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.MAGIC_SHELF
        shelf.library_id = 1
        shelf.filter_rules = {"rules": []}
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
        assert mock_book.library_id == 1

    def test_count_books_success(
        self,
        service: MagicShelfService,
        mock_shelf_repo: MagicMock,
        mock_book_repo: MagicMock,
        mock_evaluator: MagicMock,
    ) -> None:
        """Test successful counting of books from the shelf's library."""
        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.MAGIC_SHELF
        shelf.library_id = 1
        shelf.filter_rules = {"rules": []}
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
        """Test pagination is delegated to the repository."""
        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.MAGIC_SHELF
        shelf.library_id = 1
        shelf.filter_rules = {"rules": []}
        mock_shelf_repo.get.return_value = shelf

        page2_books = [MagicMock() for _ in range(5)]
        mock_book_repo.count_books_by_ids_query.return_value = 15
        mock_book_repo.list_books_by_ids_query.return_value = page2_books

        books, count = service.get_books_for_shelf(1, page=2, page_size=10)

        assert count == 15
        assert len(books) == 5
        call_kwargs = mock_book_repo.list_books_by_ids_query.call_args[1]
        assert call_kwargs["limit"] == 10
        assert call_kwargs["offset"] == 10

    def test_invalid_rules_returns_empty(
        self,
        service: MagicShelfService,
        mock_shelf_repo: MagicMock,
        mock_book_repo: MagicMock,
    ) -> None:
        """Test that invalid rules result in empty return without error."""
        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.MAGIC_SHELF
        shelf.library_id = 1
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
        shelf.library_id = 1
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
        shelf.library_id = 1
        shelf.filter_rules = None
        mock_shelf_repo.get.return_value = shelf

        mock_book_repo.count_books_by_ids_query.return_value = 0
        mock_book_repo.list_books_by_ids_query.return_value = []

        service.get_books_for_shelf(1)

        mock_evaluator.build_matching_book_ids_stmt.assert_called_once()
        args = mock_evaluator.build_matching_book_ids_stmt.call_args[0]
        assert args[0].rules == []


class TestMagicShelfServiceMultiLibrary:
    """Tests verifying that queries are scoped to the shelf's library."""

    @pytest.fixture
    def mock_shelf_repo(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_evaluator(self) -> MagicMock:
        return MagicMock()

    def test_count_scoped_to_shelf_library(
        self,
        mock_shelf_repo: MagicMock,
        mock_evaluator: MagicMock,
    ) -> None:
        """Test count_books_for_shelf only queries the shelf's library repo."""
        repo_a = MagicMock()
        repo_a.count_books_by_ids_query.return_value = 3
        repo_b = MagicMock()
        repo_b.count_books_by_ids_query.return_value = 5

        service = MagicShelfService(
            mock_shelf_repo, {1: repo_a, 2: repo_b}, mock_evaluator
        )

        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.MAGIC_SHELF
        shelf.library_id = 1
        shelf.filter_rules = {"rules": []}
        mock_shelf_repo.get.return_value = shelf

        mock_evaluator.build_matching_book_ids_stmt.return_value = "ids_query"

        count = service.count_books_for_shelf(1)
        assert count == 3
        repo_a.count_books_by_ids_query.assert_called_once_with("ids_query")
        repo_b.count_books_by_ids_query.assert_not_called()

    def test_get_books_scoped_to_shelf_library(
        self,
        mock_shelf_repo: MagicMock,
        mock_evaluator: MagicMock,
    ) -> None:
        """Test get_books_for_shelf only queries the shelf's library repo."""
        mock_book = MagicMock()
        repo_a = MagicMock()
        repo_a.count_books_by_ids_query.return_value = 1
        repo_a.list_books_by_ids_query.return_value = [mock_book]

        repo_b = MagicMock()

        service = MagicShelfService(
            mock_shelf_repo,
            {10: repo_a, 20: repo_b},
            mock_evaluator,
        )

        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.MAGIC_SHELF
        shelf.library_id = 10
        shelf.filter_rules = {"rules": []}
        mock_shelf_repo.get.return_value = shelf

        mock_evaluator.build_matching_book_ids_stmt.return_value = "ids_query"

        books, total = service.get_books_for_shelf(1)

        assert total == 1
        assert len(books) == 1
        assert mock_book.library_id == 10
        repo_b.count_books_by_ids_query.assert_not_called()
        repo_b.list_books_by_ids_query.assert_not_called()

    def test_shelf_library_not_in_repos_raises(
        self,
        mock_shelf_repo: MagicMock,
        mock_evaluator: MagicMock,
    ) -> None:
        """Test error when shelf's library has no matching repo."""
        service = MagicShelfService(mock_shelf_repo, {1: MagicMock()}, mock_evaluator)

        shelf = MagicMock(spec=Shelf)
        shelf.id = 99
        shelf.shelf_type = ShelfTypeEnum.MAGIC_SHELF
        shelf.library_id = 42
        mock_shelf_repo.get.return_value = shelf

        with pytest.raises(ValueError, match="No book repository configured"):
            service.get_books_for_shelf(99)

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
