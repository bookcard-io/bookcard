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

"""Data models for Calibre book repository.

This module contains data transfer objects and context classes used
by the Calibre book repository.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.sql import Select

    from bookcard.models.core import Book


@dataclass
class BookWithRelations:
    """Book with related author and series data.

    Attributes
    ----------
    book : Book
        Book instance.
    authors : list[str]
        List of author names.
    series : str | None
        Series name if part of a series.
    formats : list[dict[str, str | int]]
        List of file formats, each with 'format' and 'size' keys.
    """

    book: Book
    authors: list[str]
    series: str | None
    formats: list[dict[str, str | int]]


@dataclass
class BookWithFullRelations:
    """Book with all related metadata for editing.

    Attributes
    ----------
    book : Book
        Book instance.
    authors : list[str]
        List of author names.
    series : str | None
        Series name if part of a series.
    series_id : int | None
        Series ID if part of a series.
    tags : list[str]
        List of tag names.
    identifiers : list[dict[str, str]]
        List of identifiers, each with 'type' and 'val' keys.
    description : str | None
        Book description/comment text.
    publisher : str | None
        Publisher name.
    publisher_id : int | None
        Publisher ID.
    languages : list[str]
        List of language codes.
    language_ids : list[int]
        List of language IDs.
    rating : int | None
        Rating value (0-5).
    rating_id : int | None
        Rating ID.
    formats : list[dict[str, str | int]]
        List of file formats, each with 'format' and 'size' keys.
    """

    book: Book
    authors: list[str]
    series: str | None
    series_id: int | None
    tags: list[str]
    identifiers: list[dict[str, str]]
    description: str | None
    publisher: str | None
    publisher_id: int | None
    languages: list[str]
    language_ids: list[int]
    rating: int | None
    rating_id: int | None
    formats: list[dict[str, str | int]]


@dataclass
class FilterContext:
    """Context for building filter conditions.

    Attributes
    ----------
    stmt : Select
        SQLAlchemy select statement.
    or_conditions : list
        List of filter conditions to combine with OR (author, title, genre, etc.).
    and_conditions : list
        List of filter conditions to combine with AND (format, rating, language).
    """

    stmt: Select
    or_conditions: list
    and_conditions: list
