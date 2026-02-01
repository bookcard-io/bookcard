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
        return MagicShelfService(mock_shelf_repo, mock_book_repo, mock_evaluator)

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
        mock_book_repo.list_books_by_ids_query.return_value = ["book1"]
        mock_book_repo.count_books_by_ids_query.return_value = 1

        books, count = service.get_books_for_shelf(1)

        assert books == ["book1"]
        assert count == 1
        mock_book_repo.list_books_by_ids_query.assert_called_once()
        call_args = mock_book_repo.list_books_by_ids_query.call_args
        assert call_args[0][0] == "ids_query"
        call_kwargs = call_args[1]
        assert call_kwargs["limit"] == 20
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
        """Test pagination parameters are passed correctly."""
        shelf = MagicMock(spec=Shelf)
        shelf.shelf_type = ShelfTypeEnum.MAGIC_SHELF
        shelf.filter_rules = {"rules": []}
        mock_shelf_repo.get.return_value = shelf

        service.get_books_for_shelf(1, page=2, page_size=10)

        call_kwargs = mock_book_repo.list_books_by_ids_query.call_args[1]
        assert call_kwargs["limit"] == 10
        assert call_kwargs["offset"] == 10  # (2-1) * 10

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
