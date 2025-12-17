# Copyright (C) 2025 knguyen and others
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""OpenLibrary database models for Bookcard.

These models represent data imported from OpenLibrary dump files.
"""

from datetime import date
from typing import Any

from sqlalchemy import JSON, Column, Date, Index, Integer, Text, TypeDecorator
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeEngine
from sqlmodel import Field, SQLModel


class JSONBType(TypeDecorator):
    """Dialect-aware JSON type that uses JSONB for PostgreSQL and JSON for SQLite.

    This ensures compatibility with both databases while using JSONB in PostgreSQL
    for better performance and indexing capabilities.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        """Return the appropriate type based on the database dialect.

        Parameters
        ----------
        dialect : Dialect
            SQLAlchemy dialect instance.

        Returns
        -------
        TypeEngine[Any]
            JSONB for PostgreSQL, JSON for other databases.
        """
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.JSONB(astext_type=Text()))
        return dialect.type_descriptor(JSON())


class OpenLibraryAuthor(SQLModel, table=True):
    """OpenLibrary author model.

    Represents author data imported from OpenLibrary dump files.

    Attributes
    ----------
    type : str | None
        Type of the record (typically 'author').
    key : str
        Primary key identifier (OpenLibrary key, e.g., '/authors/OL123456A').
    revision : int | None
        Revision number of the record.
    last_modified : date | None
        Last modification date of the record.
    data : dict[str, Any] | None
        JSON data containing full author information.
    """

    __tablename__ = "openlibrary_authors"

    type: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    key: str = Field(sa_column=Column(Text, nullable=False, primary_key=True))
    revision: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    last_modified: date | None = Field(
        default=None, sa_column=Column(Date, nullable=True)
    )
    data: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONBType(), nullable=True),  # type: ignore[call-overload]
    )

    __table_args__ = (Index("cuix_openlibrary_authors_key", "key", unique=True),)


class OpenLibraryWork(SQLModel, table=True):
    """OpenLibrary work model.

    Represents work data imported from OpenLibrary dump files.

    Attributes
    ----------
    type : str | None
        Type of the record (typically 'work').
    key : str
        Primary key identifier (OpenLibrary key, e.g., '/works/OL123456W').
    revision : int | None
        Revision number of the record.
    last_modified : date | None
        Last modification date of the record.
    data : dict[str, Any] | None
        JSON data containing full work information.
    """

    __tablename__ = "openlibrary_works"

    type: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    key: str = Field(sa_column=Column(Text, nullable=False, primary_key=True))
    revision: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    last_modified: date | None = Field(
        default=None, sa_column=Column(Date, nullable=True)
    )
    data: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONBType(), nullable=True),  # type: ignore[call-overload]
    )

    __table_args__ = (Index("cuix_openlibrary_works_key", "key", unique=True),)


class OpenLibraryEdition(SQLModel, table=True):
    """OpenLibrary edition model.

    Represents edition data imported from OpenLibrary dump files.

    Attributes
    ----------
    type : str | None
        Type of the record (typically 'edition').
    key : str
        Primary key identifier (OpenLibrary key, e.g., '/editions/OL123456M').
    revision : int | None
        Revision number of the record.
    last_modified : date | None
        Last modification date of the record.
    data : dict[str, Any] | None
        JSON data containing full edition information.
    work_key : str | None
        Foreign key to the work this edition belongs to.
    """

    __tablename__ = "openlibrary_editions"

    type: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    key: str = Field(sa_column=Column(Text, nullable=False, primary_key=True))
    revision: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    last_modified: date | None = Field(
        default=None, sa_column=Column(Date, nullable=True)
    )
    data: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONBType(), nullable=True),  # type: ignore[call-overload]
    )
    work_key: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    __table_args__ = (
        Index("cuix_openlibrary_editions_key", "key", unique=True),
        Index("ix_openlibrary_editions_workkey", "work_key"),
    )


class OpenLibraryAuthorWork(SQLModel, table=True):
    """OpenLibrary author-work link model.

    Represents the relationship between authors and works.

    Attributes
    ----------
    author_key : str
        Foreign key to OpenLibrary author.
    work_key : str
        Foreign key to OpenLibrary work.
    """

    __tablename__ = "openlibrary_author_works"

    author_key: str = Field(sa_column=Column(Text, nullable=False, primary_key=True))
    work_key: str = Field(sa_column=Column(Text, nullable=False, primary_key=True))

    __table_args__ = (
        Index(
            "cuix_openlibrary_authorworks_authorkey_workkey",
            "author_key",
            "work_key",
            unique=True,
        ),
        Index("ix_openlibrary_authorworks_workkey", "work_key"),
        Index("ix_openlibrary_authorworks_authorkey", "author_key"),
    )


class OpenLibraryEditionIsbn(SQLModel, table=True):
    """OpenLibrary edition ISBN model.

    Represents ISBN identifiers for editions.

    Attributes
    ----------
    edition_key : str
        Foreign key to OpenLibrary edition.
    isbn : str
        ISBN identifier (can be ISBN-10 or ISBN-13).
    """

    __tablename__ = "openlibrary_edition_isbns"

    edition_key: str = Field(sa_column=Column(Text, nullable=False, primary_key=True))
    isbn: str = Field(sa_column=Column(Text, nullable=False, primary_key=True))

    __table_args__ = (
        Index(
            "cuix_openlibrary_editionisbns_editionkey_isbn",
            "edition_key",
            "isbn",
            unique=True,
        ),
        Index("ix_openlibrary_editionisbns_isbn", "isbn"),
        Index("ix_openlibrary_editionisbns_editionkey", "edition_key"),
    )
