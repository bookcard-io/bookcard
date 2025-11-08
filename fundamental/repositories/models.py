# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Data models for Calibre book repository.

This module contains data transfer objects and context classes used
by the Calibre book repository.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.sql import Select

    from fundamental.models.core import Book


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
    """

    book: Book
    authors: list[str]
    series: str | None


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
    language : str | None
        Language code.
    language_id : int | None
        Language ID.
    rating : int | None
        Rating value (0-5).
    rating_id : int | None
        Rating ID.
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
    language: str | None
    language_id: int | None
    rating: int | None
    rating_id: int | None


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
