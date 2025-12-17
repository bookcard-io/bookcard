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

"""Calibre database initialization service.

Handles creation and initialization of new Calibre SQLite databases
with all required tables and initial data.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import inspect
from sqlmodel import Session, SQLModel, create_engine

if TYPE_CHECKING:
    from sqlalchemy import Engine

# Import all Calibre models to ensure they're registered with SQLModel.metadata
from bookcard.models.core import (  # noqa: F401
    Author,
    Book,
    BookAuthorLink,
    BookLanguageLink,
    BookPublisherLink,
    BookRatingLink,
    BookSeriesLink,
    BookTagLink,
    Comment,
    Identifier,
    Language,
    Publisher,
    Rating,
    Series,
    Tag,
)
from bookcard.models.media import (  # noqa: F401
    ConversionOptions,
    Data,
)
from bookcard.models.system import (  # noqa: F401
    BookPluginData,
    CustomColumn,
    Feed,
    LibraryId,
    MetadataDirtied,
    Preference,
)

logger = logging.getLogger(__name__)

# Required Calibre tables that must exist for a valid database
REQUIRED_TABLES = {
    "authors",
    "publishers",
    "series",
    "tags",
    "languages",
    "ratings",
    "books",
    "comments",
    "identifiers",
    "books_authors_link",
    "books_languages_link",
    "books_publishers_link",
    "books_ratings_link",
    "books_series_link",
    "books_tags_link",
    "data",
    "conversion_options",
    "preferences",
    "library_id",
    "metadata_dirtied",
    "feeds",
    "custom_columns",
    "books_plugin_data",
}


class CalibreDatabaseInitializer:
    """Service for initializing new Calibre databases.

    Creates directory structure, initializes SQLite database,
    creates all required tables, and seeds initial data.
    Follows SRP by focusing solely on database initialization.
    """

    def __init__(
        self, calibre_db_path: str, calibre_db_file: str = "metadata.db"
    ) -> None:
        """Initialize the database initializer.

        Parameters
        ----------
        calibre_db_path : str
            Path to Calibre library directory (will be created if needed).
        calibre_db_file : str
            Calibre database filename (default: 'metadata.db').
        """
        self._calibre_db_path = Path(calibre_db_path)
        self._calibre_db_file = calibre_db_file
        self._db_path = self._calibre_db_path / self._calibre_db_file

    def initialize(self) -> None:
        """Initialize a new Calibre database.

        Creates the directory structure, database file, all required tables,
        and seeds initial data (library UUID, basic preferences).

        Raises
        ------
        FileExistsError
            If the database file already exists.
        PermissionError
            If the directory cannot be created or written to.
        ValueError
            If database initialization fails or validation fails.
        """
        # Check if database already exists
        if self._db_path.exists():
            msg = f"Database file already exists at {self._db_path}"
            raise FileExistsError(msg)

        # Create directory structure
        try:
            self._calibre_db_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            msg = f"Failed to create directory {self._calibre_db_path}: {e}"
            raise PermissionError(msg) from e

        # Ensure directory is writable
        if not os.access(self._calibre_db_path, os.W_OK):
            msg = f"Directory {self._calibre_db_path} is not writable"
            raise PermissionError(msg)

        # Create database engine
        db_url = f"sqlite:///{self._db_path}"
        engine = create_engine(db_url, echo=False, future=True)

        try:
            # Create all tables
            SQLModel.metadata.create_all(engine)

            # Seed initial data
            self._seed_initial_data(engine)

            # Validate database was created correctly
            self._validate_database(engine)
        except (OSError, ValueError, RuntimeError) as e:
            # Clean up on failure
            try:
                if self._db_path.exists():
                    self._db_path.unlink()
            except OSError:
                pass  # Ignore cleanup errors
            msg = f"Failed to initialize database: {e}"
            raise ValueError(msg) from e
        finally:
            engine.dispose(close=True)

    def _seed_initial_data(self, engine: Engine) -> None:
        """Seed initial data into the database.

        Parameters
        ----------
        engine : Engine
            SQLAlchemy engine instance.
        """
        # Generate library UUID
        library_uuid = str(uuid4())

        with Session(engine) as session:
            # Insert library UUID
            library_id = LibraryId(uuid=library_uuid)
            session.add(library_id)

            # Insert basic preferences (minimal set for Calibre compatibility)
            # These are common Calibre preferences that may be expected
            basic_preferences = [
                Preference(key="library_path", val=str(self._calibre_db_path)),
                Preference(key="library_uuid", val=library_uuid),
            ]

            for pref in basic_preferences:
                session.add(pref)

            session.commit()

    def _validate_database(self, engine: Engine) -> None:
        """Validate that the database was created correctly.

        Parameters
        ----------
        engine : Engine
            SQLAlchemy engine instance.

        Raises
        ------
        ValueError
            If required tables are missing.
        """
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())

        missing_tables = REQUIRED_TABLES - existing_tables
        if missing_tables:
            msg = (
                f"Database validation failed: missing required tables: "
                f"{', '.join(sorted(missing_tables))}"
            )
            raise ValueError(msg)

    @staticmethod
    def validate_existing_database(
        calibre_db_path: str,
        calibre_db_file: str = "metadata.db",
    ) -> bool:
        """Validate that an existing database is a valid Calibre database.

        Parameters
        ----------
        calibre_db_path : str
            Path to Calibre library directory.
        calibre_db_file : str
            Calibre database filename (default: 'metadata.db').

        Returns
        -------
        bool
            True if database is valid, False otherwise.
        """
        db_path = Path(calibre_db_path) / calibre_db_file

        if not db_path.exists():
            return False

        try:
            db_url = f"sqlite:///{db_path}"
            engine = create_engine(db_url, echo=False, future=True)
            try:
                inspector = inspect(engine)
                existing_tables = set(inspector.get_table_names())

                # Check if all required tables exist
                missing_tables = REQUIRED_TABLES - existing_tables
                return len(missing_tables) == 0
            finally:
                engine.dispose(close=True)
        except (OSError, ValueError, RuntimeError):
            return False
