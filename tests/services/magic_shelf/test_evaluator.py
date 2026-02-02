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

from bookcard.models.magic_shelf_rules import (
    GroupRule,
    JoinType,
    Rule,
    RuleField,
    RuleOperator,
)
from bookcard.services.magic_shelf.evaluator import BookRuleEvaluator


class TestBookRuleEvaluator:
    @pytest.fixture
    def evaluator(self) -> BookRuleEvaluator:
        return BookRuleEvaluator()

    @pytest.fixture
    def mock_registry(self, evaluator: BookRuleEvaluator) -> MagicMock:
        evaluator._operators = MagicMock()
        return evaluator._operators

    @patch("bookcard.services.magic_shelf.evaluator.select")
    def test_empty_group_returns_select_all_ids(
        self,
        mock_select: MagicMock,
        evaluator: BookRuleEvaluator,
    ) -> None:
        """Test that an empty group builds an ID select statement."""
        mock_stmt = MagicMock()
        mock_select.return_value = mock_stmt
        mock_stmt.where.return_value = mock_stmt
        mock_stmt.distinct.return_value = mock_stmt

        result = evaluator.build_matching_book_ids_stmt(GroupRule())

        assert result == mock_stmt
        mock_select.assert_called_once()
        mock_stmt.where.assert_called_once()
        mock_stmt.distinct.assert_called_once()

    @patch("bookcard.services.magic_shelf.evaluator.and_")
    def test_single_direct_rule(
        self,
        mock_and: MagicMock,
        evaluator: BookRuleEvaluator,
        mock_registry: MagicMock,
    ) -> None:
        """Test a single rule on a direct field."""
        rule = Rule(field=RuleField.TITLE, operator=RuleOperator.EQUALS, value="test")
        group = GroupRule(rules=[rule])

        mock_registry.apply.return_value = "expr"
        mock_and.return_value = "and_expr"

        with patch("bookcard.services.magic_shelf.evaluator.select") as mock_select:
            mock_stmt = MagicMock()
            mock_select.return_value = mock_stmt
            mock_stmt.where.return_value = mock_stmt
            mock_stmt.distinct.return_value = mock_stmt

            result = evaluator.build_matching_book_ids_stmt(group)

        assert result == mock_stmt
        mock_registry.apply.assert_called_once()
        mock_stmt.where.assert_called_once_with("and_expr")
        # Verify arguments to apply are correct (column, operator, value)
        # We can't easily check the column object equality without digging into definitions,
        # but we can check operator and value.
        call_args = mock_registry.apply.call_args
        assert call_args[0][1] == RuleOperator.EQUALS
        assert call_args[0][2] == "test"

    @patch("bookcard.services.magic_shelf.evaluator.or_")
    def test_or_group(
        self,
        mock_or: MagicMock,
        evaluator: BookRuleEvaluator,
        mock_registry: MagicMock,
    ) -> None:
        """Test a group with OR join type."""
        rule1 = Rule(field=RuleField.TITLE, operator=RuleOperator.EQUALS, value="a")
        rule2 = Rule(field=RuleField.TITLE, operator=RuleOperator.EQUALS, value="b")
        group = GroupRule(join_type=JoinType.OR, rules=[rule1, rule2])

        mock_registry.apply.side_effect = ["expr1", "expr2"]
        mock_or.return_value = "or_expr"

        with patch("bookcard.services.magic_shelf.evaluator.select") as mock_select:
            mock_stmt = MagicMock()
            mock_select.return_value = mock_stmt
            mock_stmt.where.return_value = mock_stmt
            mock_stmt.distinct.return_value = mock_stmt

            result = evaluator.build_matching_book_ids_stmt(group)

        assert result == mock_stmt
        mock_or.assert_called_once_with("expr1", "expr2")
        mock_stmt.where.assert_called_once_with("or_expr")

    @patch("bookcard.services.magic_shelf.evaluator.and_")
    def test_nested_groups(
        self,
        mock_and: MagicMock,
        evaluator: BookRuleEvaluator,
        mock_registry: MagicMock,
    ) -> None:
        """Test nested rule groups."""
        # (Title=a) AND ((Title=b) AND (Title=c))
        # Note: Inner group default join is AND
        inner_rule1 = Rule(
            field=RuleField.TITLE, operator=RuleOperator.EQUALS, value="b"
        )
        inner_rule2 = Rule(
            field=RuleField.TITLE, operator=RuleOperator.EQUALS, value="c"
        )
        inner_group = GroupRule(rules=[inner_rule1, inner_rule2])

        outer_rule = Rule(
            field=RuleField.TITLE, operator=RuleOperator.EQUALS, value="a"
        )
        outer_group = GroupRule(rules=[outer_rule, inner_group])

        mock_registry.apply.side_effect = ["expr_a", "expr_b", "expr_c"]
        mock_and.side_effect = ["inner_and", "outer_and"]

        with patch("bookcard.services.magic_shelf.evaluator.select") as mock_select:
            mock_stmt = MagicMock()
            mock_select.return_value = mock_stmt
            mock_stmt.where.return_value = mock_stmt
            mock_stmt.distinct.return_value = mock_stmt

            result = evaluator.build_matching_book_ids_stmt(outer_group)

        assert result == mock_stmt
        mock_stmt.where.assert_called_once_with("outer_and")
        # Verify calls
        # First call to and_ is for inner group
        # Second call to and_ is for outer group
        assert mock_and.call_count == 2

    @patch("bookcard.services.magic_shelf.evaluator.exists")
    @patch("bookcard.services.magic_shelf.evaluator.select")
    def test_related_field_rule(
        self,
        mock_select: MagicMock,
        mock_exists: MagicMock,
        evaluator: BookRuleEvaluator,
        mock_registry: MagicMock,
    ) -> None:
        """Test a rule involving a related field (e.g. Author)."""
        rule = Rule(
            field=RuleField.AUTHOR, operator=RuleOperator.CONTAINS, value="King"
        )
        group = GroupRule(rules=[rule])

        mock_registry.apply.return_value = "op_expr"
        mock_exists.return_value = "exists_expr"

        # First select() call is for related EXISTS subquery: select(1)....
        inner_stmt = MagicMock()
        inner_stmt.select_from.return_value = inner_stmt
        inner_stmt.join.return_value = inner_stmt
        inner_stmt.where.return_value = inner_stmt

        # Second select() call is for outer "select(Book.id)"
        outer_stmt = MagicMock()
        outer_stmt.where.return_value = outer_stmt
        outer_stmt.distinct.return_value = outer_stmt

        mock_select.side_effect = [inner_stmt, outer_stmt]

        with patch("bookcard.services.magic_shelf.evaluator.and_") as mock_and:
            mock_and.return_value = "and_expr"

            result = evaluator.build_matching_book_ids_stmt(group)

            assert result == outer_stmt
            outer_stmt.where.assert_called_once_with("and_expr")
            mock_exists.assert_called_once()
            mock_registry.apply.assert_called_once()
            # Verify we are applying operator to the target column (Author.name)
            # Again, hard to verify exact column object, but we check flow.

    def test_unknown_field_returns_false(
        self,
        evaluator: BookRuleEvaluator,
    ) -> None:
        """Test that unknown fields are ignored (return False)."""
        # We need to bypass validation since RuleField is an Enum
        # But if we pass a valid enum that is not in definitions map:
        # Currently all enums are in map.
        # Let's mock the definitions map.
        evaluator._fields = {}

        rule = Rule(field=RuleField.TITLE, operator=RuleOperator.EQUALS, value="test")
        group = GroupRule(rules=[rule])

        # When _evaluate_rule returns False, it gets added to expressions list
        # Then and_(*expressions) is called.

        with patch("bookcard.services.magic_shelf.evaluator.and_") as mock_and:
            with patch("bookcard.services.magic_shelf.evaluator.select") as mock_select:
                mock_stmt = MagicMock()
                mock_select.return_value = mock_stmt
                mock_stmt.where.return_value = mock_stmt
                mock_stmt.distinct.return_value = mock_stmt

                evaluator.build_matching_book_ids_stmt(group)
            mock_and.assert_called_once_with(False)
