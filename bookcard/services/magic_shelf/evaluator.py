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

"""Magic Shelf rule evaluator.

This module is responsible for translating abstract rule definitions into
SQLAlchemy expressions. It uses a configuration-driven approach to map fields
and operators to database queries.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from sqlalchemy import and_, exists, or_, select

from bookcard.models.core import Book
from bookcard.models.magic_shelf_rules import GroupRule, JoinType, Rule
from bookcard.services.magic_shelf.definitions import (
    DirectFieldDefinition,
    RelatedFieldDefinition,
    get_book_field_definitions,
)
from bookcard.services.magic_shelf.operators import OperatorRegistry

if TYPE_CHECKING:
    from sqlalchemy.sql.elements import ColumnElement

logger = logging.getLogger(__name__)


class BookRuleEvaluator:
    """Evaluates Magic Shelf rules into SQLAlchemy expressions."""

    def __init__(self) -> None:
        self._operators = OperatorRegistry()
        self._fields = get_book_field_definitions()

    def build_filter(self, group_rule: GroupRule) -> ColumnElement[bool]:
        """Build a SQLAlchemy filter expression from a GroupRule.

        Parameters
        ----------
        group_rule : GroupRule
            The root rule group to evaluate.

        Returns
        -------
        ColumnElement[bool]
            SQLAlchemy expression representing the filter.
        """
        if not group_rule.rules:
            return True  # type: ignore[return-value]

        expressions: list[ColumnElement[bool]] = []
        for item in group_rule.rules:
            if isinstance(item, GroupRule):
                expressions.append(self.build_filter(item))
            elif isinstance(item, Rule):
                expressions.append(self._evaluate_rule(item))

        if not expressions:
            return True  # type: ignore[return-value]

        if group_rule.join_type == JoinType.AND:
            return and_(*expressions)
        return or_(*expressions)

    def _evaluate_rule(self, rule: Rule) -> ColumnElement[bool]:
        """Evaluate a single rule."""
        definition = self._fields.get(rule.field)
        if not definition:
            logger.warning("No definition found for field %s", rule.field)
            return False  # type: ignore[return-value]

        if isinstance(definition, DirectFieldDefinition):
            return self._operators.apply(definition.column, rule.operator, rule.value)

        if isinstance(definition, RelatedFieldDefinition):
            return self._evaluate_related_rule(definition, rule)

        logger.warning("Unknown definition type for field %s", rule.field)
        return False  # type: ignore[return-value]

    def _evaluate_related_rule(
        self,
        definition: RelatedFieldDefinition,
        rule: Rule,
    ) -> ColumnElement[bool]:
        """Evaluate a rule involving a related table."""
        # Case 1: Many-to-Many via Link Table
        if definition.link_model is not None:
            # EXISTS (SELECT 1 FROM link_table JOIN target_table ON ... WHERE link.book = book.id AND target.col OP val)
            stmt = (
                select(1)
                .select_from(definition.link_model)
                .join(
                    definition.target_model,
                    definition.link_fk == definition.target_model.id,
                )
                .where(
                    cast("ColumnElement[bool]", definition.link_root_fk == Book.id),
                    self._operators.apply(
                        definition.target_column,
                        rule.operator,
                        rule.value,
                    ),
                )
            )
            return exists(stmt)

        # Case 2: One-to-Many (Related table has FK to Book)
        if definition.related_root_fk is not None:
            # EXISTS (SELECT 1 FROM target_table WHERE target.book = book.id AND target.col OP val)
            stmt = (
                select(1)
                .select_from(definition.target_model)
                .where(
                    cast("ColumnElement[bool]", definition.related_root_fk == Book.id),
                    self._operators.apply(
                        definition.target_column,
                        rule.operator,
                        rule.value,
                    ),
                )
            )
            return exists(stmt)

        logger.warning("Invalid related field definition for %s", rule.field)
        return False  # type: ignore[return-value]
