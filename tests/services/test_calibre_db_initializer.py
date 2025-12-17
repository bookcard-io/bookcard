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

"""Tests for calibre_db_initializer to achieve 100% coverage."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import inspect
from sqlmodel import Session, create_engine, select

from bookcard.models.system import LibraryId, Preference
from bookcard.services.calibre_db_initializer import (
    REQUIRED_TABLES,
    CalibreDatabaseInitializer,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    """Create a temporary database path for testing.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory path.

    Returns
    -------
    Path
        Temporary database path.
    """
    return tmp_path / "test_library"


@pytest.fixture
def db_file() -> str:
    """Get default database filename.

    Returns
    -------
    str
        Database filename.
    """
    return "metadata.db"


# ============================================================================
# Tests for CalibreDatabaseInitializer.__init__
# ============================================================================


class TestCalibreDatabaseInitializerInit:
    """Test CalibreDatabaseInitializer initialization."""

    def test_init_default_db_file(self, tmp_db_path: Path) -> None:
        """Test initialization with default database file.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        """
        initializer = CalibreDatabaseInitializer(str(tmp_db_path))
        assert initializer._calibre_db_path == tmp_db_path
        assert initializer._calibre_db_file == "metadata.db"
        assert initializer._db_path == tmp_db_path / "metadata.db"

    def test_init_custom_db_file(self, tmp_db_path: Path) -> None:
        """Test initialization with custom database file.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        """
        initializer = CalibreDatabaseInitializer(
            str(tmp_db_path), calibre_db_file="custom.db"
        )
        assert initializer._calibre_db_path == tmp_db_path
        assert initializer._calibre_db_file == "custom.db"
        assert initializer._db_path == tmp_db_path / "custom.db"


# ============================================================================
# Tests for CalibreDatabaseInitializer.initialize
# ============================================================================


class TestCalibreDatabaseInitializerInitialize:
    """Test initialize method."""

    def test_initialize_success(self, tmp_db_path: Path, db_file: str) -> None:
        """Test successful database initialization.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        db_file : str
            Database filename.
        """
        initializer = CalibreDatabaseInitializer(str(tmp_db_path), db_file)
        initializer.initialize()

        # Verify database file was created
        db_path = tmp_db_path / db_file
        assert db_path.exists()

        # Verify directory was created
        assert tmp_db_path.exists()

        # Verify database has required tables
        engine = create_engine(f"sqlite:///{db_path}", echo=False, future=True)
        try:
            inspector = inspect(engine)
            tables = set(inspector.get_table_names())
            assert REQUIRED_TABLES.issubset(tables)

            # Verify initial data was seeded
            with Session(engine) as session:
                stmt = select(LibraryId)
                library_id = session.exec(stmt).first()
                assert library_id is not None
                assert library_id.uuid is not None

                stmt = select(Preference).where(Preference.key == "library_path")
                pref = session.exec(stmt).first()
                assert pref is not None
                assert pref.val == str(tmp_db_path)
        finally:
            engine.dispose(close=True)

    def test_initialize_database_exists(self, tmp_db_path: Path, db_file: str) -> None:
        """Test initialize when database already exists.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        db_file : str
            Database filename.
        """
        initializer = CalibreDatabaseInitializer(str(tmp_db_path), db_file)
        db_path = tmp_db_path / db_file

        # Create the database file first
        tmp_db_path.mkdir(parents=True)
        db_path.touch()

        with pytest.raises(FileExistsError, match="Database file already exists"):
            initializer.initialize()

    def test_initialize_directory_creation_fails(
        self, tmp_db_path: Path, db_file: str
    ) -> None:
        """Test initialize when directory creation fails.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        db_file : str
            Database filename.
        """
        initializer = CalibreDatabaseInitializer(str(tmp_db_path), db_file)

        with (
            patch.object(Path, "mkdir", side_effect=OSError("Permission denied")),
            pytest.raises(PermissionError, match="Failed to create directory"),
        ):
            initializer.initialize()

    def test_initialize_directory_not_writable(
        self, tmp_db_path: Path, db_file: str
    ) -> None:
        """Test initialize when directory is not writable.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        db_file : str
            Database filename.
        """
        initializer = CalibreDatabaseInitializer(str(tmp_db_path), db_file)
        tmp_db_path.mkdir(parents=True)

        with (
            patch("os.access", return_value=False),
            pytest.raises(PermissionError, match="is not writable"),
        ):
            initializer.initialize()

    def test_initialize_database_creation_fails(
        self, tmp_db_path: Path, db_file: str
    ) -> None:
        """Test initialize when database creation fails.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        db_file : str
            Database filename.
        """
        initializer = CalibreDatabaseInitializer(str(tmp_db_path), db_file)
        tmp_db_path.mkdir(parents=True)

        with (
            patch(
                "bookcard.services.calibre_db_initializer.SQLModel.metadata.create_all",
                side_effect=RuntimeError("Table creation failed"),
            ),
            pytest.raises(ValueError, match="Failed to initialize database"),
        ):
            initializer.initialize()

        # Verify cleanup - database file should not exist
        db_path = tmp_db_path / db_file
        assert not db_path.exists()

    def test_initialize_validation_fails(self, tmp_db_path: Path, db_file: str) -> None:
        """Test initialize when validation fails.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        db_file : str
            Database filename.
        """
        initializer = CalibreDatabaseInitializer(str(tmp_db_path), db_file)
        tmp_db_path.mkdir(parents=True)

        with patch("bookcard.services.calibre_db_initializer.inspect") as mock_inspect:
            mock_inspector = MagicMock()
            mock_inspector.get_table_names.return_value = []  # No tables
            mock_inspect.return_value = mock_inspector

            with pytest.raises(ValueError, match="Failed to initialize database"):
                initializer.initialize()

        # Verify cleanup
        db_path = tmp_db_path / db_file
        assert not db_path.exists()

    def test_initialize_cleanup_on_failure(
        self, tmp_db_path: Path, db_file: str
    ) -> None:
        """Test initialize cleans up database file on failure.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        db_file : str
            Database filename.
        """
        initializer = CalibreDatabaseInitializer(str(tmp_db_path), db_file)
        tmp_db_path.mkdir(parents=True)
        db_path = tmp_db_path / db_file

        # Initialize and let it create the file, then simulate failure
        with (
            patch(
                "bookcard.services.calibre_db_initializer.SQLModel.metadata.create_all",
                side_effect=ValueError("Database error"),
            ),
            pytest.raises(ValueError, match="Failed to initialize database"),
        ):
            initializer.initialize()

        # Verify cleanup - database file should not exist
        db_path = tmp_db_path / db_file
        assert not db_path.exists()

    def test_initialize_cleanup_ignores_oserror(
        self, tmp_db_path: Path, db_file: str
    ) -> None:
        """Test initialize cleanup ignores OSError when removing file.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        db_file : str
            Database filename.
        """
        initializer = CalibreDatabaseInitializer(str(tmp_db_path), db_file)
        tmp_db_path.mkdir(parents=True)

        # Patch _validate_database to fail after file is created
        with (
            patch.object(
                initializer,
                "_validate_database",
                side_effect=ValueError("Validation failed"),
            ),
            patch.object(Path, "unlink", side_effect=OSError("Cannot delete")),
            pytest.raises(ValueError, match="Failed to initialize database"),
        ):
            # Should not raise OSError from cleanup
            initializer.initialize()


# ============================================================================
# Tests for CalibreDatabaseInitializer._seed_initial_data
# ============================================================================


class TestCalibreDatabaseInitializerSeedInitialData:
    """Test _seed_initial_data method."""

    def test_seed_initial_data(self, tmp_db_path: Path, db_file: str) -> None:
        """Test seeding initial data.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        db_file : str
            Database filename.
        """
        initializer = CalibreDatabaseInitializer(str(tmp_db_path), db_file)
        tmp_db_path.mkdir(parents=True)
        db_path = tmp_db_path / db_file

        # Create minimal database
        engine = create_engine(f"sqlite:///{db_path}", echo=False, future=True)
        try:
            from sqlmodel import SQLModel

            SQLModel.metadata.create_all(engine)

            # Seed data
            initializer._seed_initial_data(engine)

            # Verify data was seeded
            with Session(engine) as session:
                stmt = select(LibraryId)
                library_id = session.exec(stmt).first()
                assert library_id is not None
                assert library_id.uuid is not None

                stmt = select(Preference).where(Preference.key == "library_path")
                pref = session.exec(stmt).first()
                assert pref is not None
                assert pref.val == str(tmp_db_path)

                stmt = select(Preference).where(Preference.key == "library_uuid")
                uuid_pref = session.exec(stmt).first()
                assert uuid_pref is not None
                assert uuid_pref.val == library_id.uuid
        finally:
            engine.dispose(close=True)


# ============================================================================
# Tests for CalibreDatabaseInitializer._validate_database
# ============================================================================


class TestCalibreDatabaseInitializerValidateDatabase:
    """Test _validate_database method."""

    def test_validate_database_success(self, tmp_db_path: Path, db_file: str) -> None:
        """Test validation succeeds with all required tables.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        db_file : str
            Database filename.
        """
        initializer = CalibreDatabaseInitializer(str(tmp_db_path), db_file)
        tmp_db_path.mkdir(parents=True)
        db_path = tmp_db_path / db_file

        engine = create_engine(f"sqlite:///{db_path}", echo=False, future=True)
        try:
            from sqlmodel import SQLModel

            SQLModel.metadata.create_all(engine)

            # Should not raise
            initializer._validate_database(engine)
        finally:
            engine.dispose(close=True)

    def test_validate_database_missing_tables(
        self, tmp_db_path: Path, db_file: str
    ) -> None:
        """Test validation fails when tables are missing.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        db_file : str
            Database filename.
        """
        initializer = CalibreDatabaseInitializer(str(tmp_db_path), db_file)
        tmp_db_path.mkdir(parents=True)
        db_path = tmp_db_path / db_file

        # Create empty database
        engine = create_engine(f"sqlite:///{db_path}", echo=False, future=True)
        try:
            with pytest.raises(ValueError, match="Database validation failed"):
                initializer._validate_database(engine)
        finally:
            engine.dispose(close=True)


# ============================================================================
# Tests for CalibreDatabaseInitializer.validate_existing_database
# ============================================================================


class TestCalibreDatabaseInitializerValidateExistingDatabase:
    """Test validate_existing_database static method."""

    def test_validate_existing_database_success(
        self, tmp_db_path: Path, db_file: str
    ) -> None:
        """Test validation succeeds for valid existing database.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        db_file : str
            Database filename.
        """
        initializer = CalibreDatabaseInitializer(str(tmp_db_path), db_file)
        initializer.initialize()

        result = CalibreDatabaseInitializer.validate_existing_database(
            str(tmp_db_path), db_file
        )
        assert result is True

    def test_validate_existing_database_not_exists(
        self, tmp_db_path: Path, db_file: str
    ) -> None:
        """Test validation returns False when database doesn't exist.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        db_file : str
            Database filename.
        """
        result = CalibreDatabaseInitializer.validate_existing_database(
            str(tmp_db_path), db_file
        )
        assert result is False

    def test_validate_existing_database_missing_tables(
        self, tmp_db_path: Path, db_file: str
    ) -> None:
        """Test validation returns False when tables are missing.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        db_file : str
            Database filename.
        """
        tmp_db_path.mkdir(parents=True)
        db_path = tmp_db_path / db_file

        # Create empty database file
        db_path.touch()

        result = CalibreDatabaseInitializer.validate_existing_database(
            str(tmp_db_path), db_file
        )
        assert result is False

    def test_validate_existing_database_oserror(
        self, tmp_db_path: Path, db_file: str
    ) -> None:
        """Test validation returns False on OSError.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        db_file : str
            Database filename.
        """
        with patch(
            "bookcard.services.calibre_db_initializer.create_engine",
            side_effect=OSError("Cannot open"),
        ):
            result = CalibreDatabaseInitializer.validate_existing_database(
                str(tmp_db_path), db_file
            )
            assert result is False

    def test_validate_existing_database_valueerror(
        self, tmp_db_path: Path, db_file: str
    ) -> None:
        """Test validation returns False on ValueError.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        db_file : str
            Database filename.
        """
        tmp_db_path.mkdir(parents=True)
        db_path = tmp_db_path / db_file
        db_path.touch()

        with patch(
            "bookcard.services.calibre_db_initializer.inspect",
            side_effect=ValueError("Invalid database"),
        ):
            result = CalibreDatabaseInitializer.validate_existing_database(
                str(tmp_db_path), db_file
            )
            assert result is False

    def test_validate_existing_database_runtimeerror(
        self, tmp_db_path: Path, db_file: str
    ) -> None:
        """Test validation returns False on RuntimeError.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        db_file : str
            Database filename.
        """
        tmp_db_path.mkdir(parents=True)
        db_path = tmp_db_path / db_file
        db_path.touch()

        with patch(
            "bookcard.services.calibre_db_initializer.create_engine",
            side_effect=RuntimeError("Engine error"),
        ):
            result = CalibreDatabaseInitializer.validate_existing_database(
                str(tmp_db_path), db_file
            )
            assert result is False

    def test_validate_existing_database_custom_file(self, tmp_db_path: Path) -> None:
        """Test validation with custom database filename.

        Parameters
        ----------
        tmp_db_path : Path
            Temporary database path.
        """
        custom_file = "custom.db"
        initializer = CalibreDatabaseInitializer(str(tmp_db_path), custom_file)
        initializer.initialize()

        result = CalibreDatabaseInitializer.validate_existing_database(
            str(tmp_db_path), custom_file
        )
        assert result is True
