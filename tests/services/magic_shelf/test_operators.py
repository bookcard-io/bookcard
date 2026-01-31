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

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import Column

from bookcard.models.magic_shelf_rules import RuleOperator
from bookcard.services.magic_shelf.operators import OperatorRegistry


class TestOperatorRegistry:
    @pytest.fixture
    def registry(self) -> OperatorRegistry:
        return OperatorRegistry()

    @pytest.fixture
    def mock_column(self) -> MagicMock:
        col = MagicMock(spec=Column)
        # Setup return values for common operators to return a mock expression
        col.__eq__.return_value = "eq_expr"
        col.__ne__.return_value = "ne_expr"
        col.__gt__.return_value = "gt_expr"
        col.__lt__.return_value = "lt_expr"
        col.__ge__.return_value = "ge_expr"
        col.__le__.return_value = "le_expr"
        col.ilike.return_value = "ilike_expr"
        col.in_.return_value = "in_expr"
        col.notin_.return_value = "notin_expr"
        col.is_.return_value = "is_expr"
        col.is_not.return_value = "is_not_expr"
        return col

    @pytest.mark.parametrize(
        ("operator", "value", "expected_method"),
        [
            (RuleOperator.EQUALS, "val", "__eq__"),
            (RuleOperator.NOT_EQUALS, "val", "__ne__"),
            (RuleOperator.GREATER_THAN, 10, "__gt__"),
            (RuleOperator.LESS_THAN, 10, "__lt__"),
            (RuleOperator.GREATER_THAN_OR_EQUALS, 10, "__ge__"),
            (RuleOperator.LESS_THAN_OR_EQUALS, 10, "__le__"),
        ],
    )
    def test_comparison_operators(
        self,
        registry: OperatorRegistry,
        mock_column: MagicMock,
        operator: RuleOperator,
        value: str | int,
        expected_method: str,
    ) -> None:
        """Test basic comparison operators."""
        registry.apply(mock_column, operator, value)
        getattr(mock_column, expected_method).assert_called_once_with(value)

    @pytest.mark.parametrize(
        ("operator", "value", "expected_pattern"),
        [
            (RuleOperator.CONTAINS, "foo", "%foo%"),
            (RuleOperator.NOT_CONTAINS, "foo", "%foo%"),
            (RuleOperator.STARTS_WITH, "foo", "foo%"),
            (RuleOperator.ENDS_WITH, "foo", "%foo"),
        ],
    )
    def test_string_pattern_operators(
        self,
        registry: OperatorRegistry,
        mock_column: MagicMock,
        operator: RuleOperator,
        value: str,
        expected_pattern: str,
    ) -> None:
        """Test string pattern matching operators (ilike)."""
        registry.apply(mock_column, operator, value)
        mock_column.ilike.assert_called_once_with(expected_pattern)

    def test_in_operator(
        self,
        registry: OperatorRegistry,
        mock_column: MagicMock,
    ) -> None:
        """Test IN operator."""
        value = ["a", "b"]
        registry.apply(mock_column, RuleOperator.IN, value)
        mock_column.in_.assert_called_once_with(value)

    def test_not_in_operator(
        self,
        registry: OperatorRegistry,
        mock_column: MagicMock,
    ) -> None:
        """Test NOT IN operator."""
        value = ["a", "b"]
        registry.apply(mock_column, RuleOperator.NOT_IN, value)
        mock_column.notin_.assert_called_once_with(value)

    @patch("bookcard.services.magic_shelf.operators.or_")
    def test_is_empty_operator(
        self,
        mock_or: MagicMock,
        registry: OperatorRegistry,
        mock_column: MagicMock,
    ) -> None:
        """Test IS_EMPTY operator."""
        mock_or.return_value = "or_expr"
        result = registry.apply(mock_column, RuleOperator.IS_EMPTY, None)

        assert result == "or_expr"
        mock_column.is_.assert_called_once_with(None)
        mock_column.__eq__.assert_called_once_with("")
        mock_or.assert_called_once_with("is_expr", "eq_expr")

    @patch("bookcard.services.magic_shelf.operators.and_")
    def test_is_not_empty_operator(
        self,
        mock_and: MagicMock,
        registry: OperatorRegistry,
        mock_column: MagicMock,
    ) -> None:
        """Test IS_NOT_EMPTY operator."""
        mock_and.return_value = "and_expr"
        result = registry.apply(mock_column, RuleOperator.IS_NOT_EMPTY, None)

        assert result == "and_expr"
        mock_column.is_not.assert_called_once_with(None)
        mock_column.__ne__.assert_called_once_with("")
        mock_and.assert_called_once_with("is_not_expr", "ne_expr")

    def test_invalid_operator(
        self,
        registry: OperatorRegistry,
        mock_column: MagicMock,
    ) -> None:
        """Test handling of invalid/unsupported operator."""
        # Force an invalid operator enum or just a string if type checking allows
        # But here we can just test the safety check if we pass something not in the map
        # Since RuleOperator is an Enum, we can't easily pass an invalid one unless we cast.
        # However, if we add a new operator to Enum but forget to add to registry:

        # Let's mock the strategies dict to simulate a missing strategy
        registry._strategies = {}
        result = registry.apply(mock_column, RuleOperator.EQUALS, "val")
        assert result is False

    def test_none_value_for_value_required_operators(
        self,
        registry: OperatorRegistry,
        mock_column: MagicMock,
    ) -> None:
        """Test that operators requiring a value return False if value is None."""
        result = registry.apply(mock_column, RuleOperator.EQUALS, None)
        assert result is False
