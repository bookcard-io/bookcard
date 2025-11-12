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

"""Core database models for Fundamental."""

from datetime import UTC, datetime

from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel


class Author(SQLModel, table=True):
    """Author model for book authors.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    name : str
        Author name.
    sort : Optional[str]
        Sort name for author.
    link : str
        Link field (default empty string).
    """

    __tablename__ = "authors"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    sort: str | None = None
    link: str = ""


class Publisher(SQLModel, table=True):
    """Publisher model for book publishers.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    name : str
        Publisher name.
    sort : Optional[str]
        Sort name for publisher.
    link : str
        Link field (default empty string).
    """

    __tablename__ = "publishers"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    sort: str | None = None
    link: str = ""


class Series(SQLModel, table=True):
    """Series model for book series.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    name : str
        Series name.
    sort : Optional[str]
        Sort name for series.
    link : str
        Link field (default empty string).
    """

    __tablename__ = "series"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    sort: str | None = None
    link: str = ""


class Tag(SQLModel, table=True):
    """Tag model for book tags.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    name : str
        Tag name.
    link : str
        Link field (default empty string).
    """

    __tablename__ = "tags"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    link: str = ""


class Language(SQLModel, table=True):
    """Language model for book languages.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    lang_code : str
        Language code (e.g., 'en', 'fr').
    link : str
        Link field (default empty string).
    """

    __tablename__ = "languages"

    id: int | None = Field(default=None, primary_key=True)
    lang_code: str
    link: str = ""


class Rating(SQLModel, table=True):
    """Rating model for book ratings.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    rating : Optional[int]
        Rating value.
    link : str
        Link field (default empty string).
    """

    __tablename__ = "ratings"

    id: int | None = Field(default=None, primary_key=True)
    rating: int | None = None
    link: str = ""


class Book(SQLModel, table=True):
    """Book model representing the core book entity.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    title : str
        Book title (default 'Unknown').
    sort : Optional[str]
        Sort title for book.
    timestamp : Optional[datetime]
        Timestamp when book was added.
    pubdate : Optional[datetime]
        Publication date.
    series_index : float
        Index within series (default 1.0).
    author_sort : Optional[str]
        Sort string for authors.
    isbn : str
        ISBN identifier (default empty string).
    lccn : str
        LCCN identifier (default empty string).
    path : str
        File path to book (default empty string).
    flags : int
        Book flags (default 1).
    uuid : Optional[str]
        Unique identifier for book.
    has_cover : bool
        Whether book has cover image (default False).
    last_modified : datetime
        Last modification timestamp.
    """

    __tablename__ = "books"

    id: int | None = Field(default=None, primary_key=True)
    title: str = "Unknown"
    sort: str | None = None
    timestamp: datetime | None = Field(
        default_factory=lambda: datetime.now(UTC),
    )
    pubdate: datetime | None = Field(
        default_factory=lambda: datetime.now(UTC),
    )
    series_index: float = 1.0
    author_sort: str | None = None
    isbn: str = ""
    lccn: str = ""
    path: str = ""
    flags: int = 1
    uuid: str | None = Field(
        default=None,
        sa_column=Column(String, nullable=True),
    )
    has_cover: bool = False
    last_modified: datetime = Field(
        default_factory=lambda: datetime(2000, 1, 1, tzinfo=UTC),
    )


class Comment(SQLModel, table=True):
    """Comment model for book descriptions/comments.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    book : int
        Foreign key to book.
    text : str
        Comment/description text.
    """

    __tablename__ = "comments"

    id: int | None = Field(default=None, primary_key=True)
    book: int = Field(foreign_key="books.id")
    text: str


class Identifier(SQLModel, table=True):
    """Identifier model for book identifiers (ISBN, DOI, etc.).

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    book : int
        Foreign key to book.
    type : str
        Identifier type (default 'isbn').
    val : str
        Identifier value.
    """

    __tablename__ = "identifiers"

    id: int | None = Field(default=None, primary_key=True)
    book: int = Field(foreign_key="books.id")
    type: str = "isbn"
    val: str


# Link/Junction tables for many-to-many relationships


class BookAuthorLink(SQLModel, table=True):
    """Link table for books and authors many-to-many relationship.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    book : int
        Foreign key to book.
    author : int
        Foreign key to author.
    """

    __tablename__ = "books_authors_link"

    id: int | None = Field(default=None, primary_key=True)
    book: int = Field(foreign_key="books.id")
    author: int = Field(foreign_key="authors.id")


class BookLanguageLink(SQLModel, table=True):
    """Link table for books and languages many-to-many relationship.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    book : int
        Foreign key to book.
    lang_code : int
        Foreign key to language.
    item_order : int
        Order of language in list (default 0).
    """

    __tablename__ = "books_languages_link"

    id: int | None = Field(default=None, primary_key=True)
    book: int = Field(foreign_key="books.id")
    lang_code: int = Field(foreign_key="languages.id")
    item_order: int = 0


class BookPublisherLink(SQLModel, table=True):
    """Link table for books and publishers many-to-many relationship.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    book : int
        Foreign key to book.
    publisher : int
        Foreign key to publisher.
    """

    __tablename__ = "books_publishers_link"

    id: int | None = Field(default=None, primary_key=True)
    book: int = Field(foreign_key="books.id")
    publisher: int = Field(foreign_key="publishers.id")


class BookRatingLink(SQLModel, table=True):
    """Link table for books and ratings many-to-many relationship.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    book : int
        Foreign key to book.
    rating : int
        Foreign key to rating.
    """

    __tablename__ = "books_ratings_link"

    id: int | None = Field(default=None, primary_key=True)
    book: int = Field(foreign_key="books.id")
    rating: int = Field(foreign_key="ratings.id")


class BookSeriesLink(SQLModel, table=True):
    """Link table for books and series many-to-many relationship.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    book : int
        Foreign key to book.
    series : int
        Foreign key to series.
    """

    __tablename__ = "books_series_link"

    id: int | None = Field(default=None, primary_key=True)
    book: int = Field(foreign_key="books.id")
    series: int = Field(foreign_key="series.id")


class BookTagLink(SQLModel, table=True):
    """Link table for books and tags many-to-many relationship.

    Attributes
    ----------
    id : Optional[int]
        Primary key identifier.
    book : int
        Foreign key to book.
    tag : int
        Foreign key to tag.
    """

    __tablename__ = "books_tags_link"

    id: int | None = Field(default=None, primary_key=True)
    book: int = Field(foreign_key="books.id")
    tag: int = Field(foreign_key="tags.id")
