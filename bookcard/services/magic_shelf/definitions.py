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

"""Field definitions for Magic Shelf rules.

This module defines how abstract RuleFields map to database models and columns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bookcard.models.core import (
    Author,
    Book,
    BookAuthorLink,
    BookLanguageLink,
    BookPublisherLink,
    BookRatingLink,
    BookSeriesLink,
    BookTagLink,
    Identifier,
    Language,
    Publisher,
    Rating,
    Series,
    Tag,
)
from bookcard.models.magic_shelf_rules import RuleField


@dataclass(frozen=True)
class FieldDefinition:
    """Base class for field definitions."""

    field: RuleField


@dataclass(frozen=True)
class DirectFieldDefinition(FieldDefinition):
    """Definition for fields that map directly to a column on the Book model."""

    column: Any


@dataclass(frozen=True)
class RelatedFieldDefinition(FieldDefinition):
    """Definition for fields that require a join to a related table."""

    target_model: Any
    target_column: Any
    # For Many-to-Many relationships (via Link table)
    link_model: Any | None = None
    link_fk: Any | None = None  # Column in link table pointing to target
    link_root_fk: Any | None = None  # Column in link table pointing to Book
    # For One-to-Many relationships (Direct FK on related table)
    related_root_fk: Any | None = None  # Column in related table pointing to Book


def get_book_field_definitions() -> dict[RuleField, FieldDefinition]:
    """Get the standard field definitions for Books."""
    return {
        # Direct Fields
        RuleField.TITLE: DirectFieldDefinition(
            field=RuleField.TITLE,
            column=Book.title,
        ),
        RuleField.PUBDATE: DirectFieldDefinition(
            field=RuleField.PUBDATE,
            column=Book.pubdate,
        ),
        RuleField.ISBN: DirectFieldDefinition(
            field=RuleField.ISBN,
            column=Book.isbn,
        ),
        # Many-to-Many Relationships
        RuleField.AUTHOR: RelatedFieldDefinition(
            field=RuleField.AUTHOR,
            target_model=Author,
            target_column=Author.name,
            link_model=BookAuthorLink,
            link_fk=BookAuthorLink.author,
            link_root_fk=BookAuthorLink.book,
        ),
        RuleField.TAG: RelatedFieldDefinition(
            field=RuleField.TAG,
            target_model=Tag,
            target_column=Tag.name,
            link_model=BookTagLink,
            link_fk=BookTagLink.tag,
            link_root_fk=BookTagLink.book,
        ),
        RuleField.SERIES: RelatedFieldDefinition(
            field=RuleField.SERIES,
            target_model=Series,
            target_column=Series.name,
            link_model=BookSeriesLink,
            link_fk=BookSeriesLink.series,
            link_root_fk=BookSeriesLink.book,
        ),
        RuleField.PUBLISHER: RelatedFieldDefinition(
            field=RuleField.PUBLISHER,
            target_model=Publisher,
            target_column=Publisher.name,
            link_model=BookPublisherLink,
            link_fk=BookPublisherLink.publisher,
            link_root_fk=BookPublisherLink.book,
        ),
        RuleField.LANGUAGE: RelatedFieldDefinition(
            field=RuleField.LANGUAGE,
            target_model=Language,
            target_column=Language.lang_code,
            link_model=BookLanguageLink,
            link_fk=BookLanguageLink.lang_code,
            link_root_fk=BookLanguageLink.book,
        ),
        RuleField.RATING: RelatedFieldDefinition(
            field=RuleField.RATING,
            target_model=Rating,
            target_column=Rating.rating,
            link_model=BookRatingLink,
            link_fk=BookRatingLink.rating,
            link_root_fk=BookRatingLink.book,
        ),
        # One-to-Many Relationship (Identifier -> Book)
        RuleField.IDENTIFIER: RelatedFieldDefinition(
            field=RuleField.IDENTIFIER,
            target_model=Identifier,
            target_column=Identifier.val,
            related_root_fk=Identifier.book,
        ),
    }
