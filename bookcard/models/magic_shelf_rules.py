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

"""Magic Shelf rule definitions.

This module defines the schema for Magic Shelf filter rules using Pydantic.
It strictly adheres to SRP by focusing solely on data structure and validation.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class RuleOperator(StrEnum):
    """Operators for rule evaluation."""

    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    STARTS_WITH = "STARTS_WITH"
    ENDS_WITH = "ENDS_WITH"
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    GREATER_THAN_OR_EQUALS = "GREATER_THAN_OR_EQUALS"
    LESS_THAN_OR_EQUALS = "LESS_THAN_OR_EQUALS"
    IN = "IN"
    NOT_IN = "NOT_IN"
    IS_EMPTY = "IS_EMPTY"
    IS_NOT_EMPTY = "IS_NOT_EMPTY"


class RuleField(StrEnum):
    """Fields supported for filtering."""

    TITLE = "TITLE"
    AUTHOR = "AUTHOR"
    TAG = "TAG"
    SERIES = "SERIES"
    PUBLISHER = "PUBLISHER"
    LANGUAGE = "LANGUAGE"
    RATING = "RATING"
    PUBDATE = "PUBDATE"
    IDENTIFIER = "IDENTIFIER"
    ISBN = "ISBN"
    # Can be extended without breaking existing rules (OCP)


class JoinType(StrEnum):
    """Logical operators for combining rules."""

    AND = "AND"
    OR = "OR"


class Rule(BaseModel):
    """A single filter rule."""

    field: RuleField
    operator: RuleOperator
    value: str | int | float | list[str] | list[int] | None = None


class GroupRule(BaseModel):
    """A group of rules combined with a logical operator."""

    join_type: JoinType = JoinType.AND
    rules: list[Rule | GroupRule] = Field(default_factory=list)


# Resolve forward reference for recursive model
GroupRule.model_rebuild()
