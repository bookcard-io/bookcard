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

"""Operator logic for Magic Shelf rules.

This module encapsulates the strategy for applying operators to SQLAlchemy columns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import and_, not_, or_

from bookcard.models.magic_shelf_rules import RuleOperator

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.sql.elements import ColumnElement


class OperatorRegistry:
    """Registry for rule operator strategies."""

    def __init__(self) -> None:
        self._strategies: dict[
            RuleOperator,
            Callable[[ColumnElement[Any], Any], ColumnElement[bool]],
        ] = {
            RuleOperator.EQUALS: lambda c, v: c == v,
            RuleOperator.NOT_EQUALS: lambda c, v: c != v,
            RuleOperator.CONTAINS: lambda c, v: c.ilike(f"%{v}%"),
            RuleOperator.NOT_CONTAINS: lambda c, v: not_(c.ilike(f"%{v}%")),
            RuleOperator.STARTS_WITH: lambda c, v: c.ilike(f"{v}%"),
            RuleOperator.ENDS_WITH: lambda c, v: c.ilike(f"%{v}"),
            RuleOperator.GREATER_THAN: lambda c, v: c > v,
            RuleOperator.LESS_THAN: lambda c, v: c < v,
            RuleOperator.GREATER_THAN_OR_EQUALS: lambda c, v: c >= v,
            RuleOperator.LESS_THAN_OR_EQUALS: lambda c, v: c <= v,
            RuleOperator.IN: self._handle_in,
            RuleOperator.NOT_IN: self._handle_not_in,
        }

    def apply(
        self,
        column: object,
        operator: RuleOperator,
        value: object,
    ) -> ColumnElement[bool]:
        """Apply an operator to a column with a value.

        Parameters
        ----------
        column : object
            The SQLAlchemy column or expression.
        operator : RuleOperator
            The operator to apply.
        value : Any
            The value to compare against.

        Returns
        -------
        ColumnElement[bool]
            The resulting SQLAlchemy expression.
        """
        col = cast("ColumnElement[Any]", column)

        # Handle null/empty checks which don't use the value
        if operator == RuleOperator.IS_EMPTY:
            return or_(col.is_(None), col == "")
        if operator == RuleOperator.IS_NOT_EMPTY:
            return and_(col.is_not(None), col != "")

        # For other operators, value is required
        if value is None:
            return False  # type: ignore[return-value]

        strategy = self._strategies.get(operator)
        if not strategy:
            return False  # type: ignore[return-value]

        return strategy(col, value)

    def _handle_in(self, col: ColumnElement[Any], value: object) -> ColumnElement[bool]:
        if isinstance(value, list):
            return col.in_(value)
        return False  # type: ignore[return-value]

    def _handle_not_in(
        self, col: ColumnElement[Any], value: object
    ) -> ColumnElement[bool]:
        if isinstance(value, list):
            return col.notin_(value)
        return False  # type: ignore[return-value]
