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

"""Configuration service.

Business logic for managing system configuration settings.
"""

import logging
import os
import re
from pathlib import Path

from sqlmodel import Session, select

from bookcard.config import AppConfig
from bookcard.models.config import (
    BasicConfig,
    EPUBFixerConfig,
    FileHandlingConfig,
    Library,
    ScheduledJobDefinition,
    ScheduledTasksConfig,
)
from bookcard.models.tasks import TaskType
from bookcard.repositories.calibre_book_repository import (
    CalibreBookRepository,
)
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.repositories.shelf_repository import ShelfRepository
from bookcard.services.calibre_db_initializer import (
    CalibreDatabaseInitializer,
)

logger = logging.getLogger(__name__)


class BasicConfigService:
    """Service for managing basic system configuration."""

    def __init__(self, session: Session) -> None:  # type: ignore[type-arg]
        """Initialize the basic configuration service.

        Parameters
        ----------
        session : Session
            Active SQLModel session.
        """
        self._session = session

    def get_basic_config(self) -> BasicConfig:
        """Get the singleton basic configuration, creating defaults if missing."""
        stmt = select(BasicConfig).limit(1)
        config = self._session.exec(stmt).first()
        if config is None:
            config = BasicConfig()
            self._session.add(config)
            self._session.commit()
            self._session.refresh(config)
        return config

    def update_basic_config(
        self,
        *,
        allow_anonymous_browsing: bool | None = None,
        allow_public_registration: bool | None = None,
        require_email_for_registration: bool | None = None,
        max_upload_size_mb: int | None = None,
    ) -> BasicConfig:
        """Update basic configuration flags.

        Parameters
        ----------
        allow_anonymous_browsing : bool | None
            Optional toggle for anonymous browsing.
        allow_public_registration : bool | None
            Optional toggle for public registration.
        require_email_for_registration : bool | None
            Optional toggle for requiring email during registration.
        max_upload_size_mb : int | None
            Optional maximum upload size in megabytes.

        Returns
        -------
        BasicConfig
            Updated configuration record.
        """
        config = self.get_basic_config()
        if allow_anonymous_browsing is not None:
            config.allow_anonymous_browsing = allow_anonymous_browsing
        if allow_public_registration is not None:
            config.allow_public_registration = allow_public_registration
        if require_email_for_registration is not None:
            config.require_email_for_registration = require_email_for_registration
        if max_upload_size_mb is not None:
            config.max_upload_size_mb = max_upload_size_mb
        self._session.add(config)
        self._session.commit()
        self._session.refresh(config)
        return config


class LibraryService:
    """Operations for managing Calibre libraries.

    Parameters
    ----------
    session : Session
        Active SQLModel session.
    library_repo : LibraryRepository
        Repository for library persistence operations.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        library_repo: LibraryRepository,  # type: ignore[type-arg]
    ) -> None:
        self._session = session
        self._library_repo = library_repo

    def list_libraries(self) -> list[Library]:
        """List all libraries.

        Returns
        -------
        list[Library]
            All libraries.
        """
        return self._library_repo.list_all()

    def get_active_library(self) -> Library | None:
        """Get the currently active library.

        Returns
        -------
        Library | None
            The active library if one exists, None otherwise.
        """
        return self._library_repo.get_active()

    def require_active_library(self) -> Library:
        """Get the currently active library, raising exception if not found.

        Returns
        -------
        Library
            The active library.

        Raises
        ------
        ValueError
            If no active library is configured.
        """
        library = self.get_active_library()
        if library is None:
            msg = "No active library configured"
            raise ValueError(msg)
        return library

    def get_library(self, library_id: int) -> Library | None:
        """Get a library by ID.

        Parameters
        ----------
        library_id : int
            Library identifier.

        Returns
        -------
        Library | None
            Library if found, None otherwise.
        """
        return self._library_repo.get(library_id)

    def create_library(
        self,
        name: str,
        calibre_db_path: str | None = None,
        *,
        calibre_db_file: str = "metadata.db",
        use_split_library: bool = False,
        split_library_dir: str | None = None,
        auto_reconnect: bool = True,
        auto_metadata_enforcement: bool = True,
        is_active: bool = False,
    ) -> Library:
        """Create a new library.

        Parameters
        ----------
        name : str
            User-friendly library name.
        calibre_db_path : str | None
            Path to Calibre database directory. If None, auto-generates from name.
        calibre_db_file : str
            Calibre database filename (default: 'metadata.db').
        use_split_library : bool
            Whether to use split library mode (default: False).
        split_library_dir : str | None
            Directory for split library mode.
        auto_reconnect : bool
            Whether to automatically reconnect on errors (default: True).
        is_active : bool
            Whether to set this as the active library (default: False).

        Returns
        -------
        Library
            Created library.

        Raises
        ------
        ValueError
            If a library with the same path already exists, or if database
            initialization fails.
        PermissionError
            If directory cannot be created or written to.
        """
        # Auto-generate path if not provided
        if calibre_db_path is None:
            calibre_db_path = self._generate_library_path(name)
        else:
            # Parse file path if user provided a full file path
            calibre_db_path, calibre_db_file = self._parse_library_path(
                calibre_db_path, calibre_db_file
            )

        # Check if path already exists in our records
        existing = self._library_repo.find_by_path(calibre_db_path)
        if existing is not None:
            msg = "library_path_already_exists"
            raise ValueError(msg)

        # Check if database file exists
        db_path = Path(calibre_db_path) / calibre_db_file
        if db_path.exists():
            # Validate existing database
            if not CalibreDatabaseInitializer.validate_existing_database(
                calibre_db_path, calibre_db_file
            ):
                msg = f"Invalid Calibre database at {db_path}"
                raise ValueError(msg)
        else:
            # Initialize new database
            try:
                initializer = CalibreDatabaseInitializer(
                    calibre_db_path, calibre_db_file
                )
                initializer.initialize()
                logger.info("Initialized new Calibre database at %s", calibre_db_path)
            except FileExistsError:
                # Database was created between check and initialization
                # Validate it's a valid database
                if not CalibreDatabaseInitializer.validate_existing_database(
                    calibre_db_path, calibre_db_file
                ):
                    msg = f"Invalid Calibre database at {db_path}"
                    raise ValueError(msg) from None
            except (PermissionError, ValueError) as e:
                msg = f"Failed to initialize database: {e}"
                raise ValueError(msg) from e

        # If setting as active, deactivate all others
        if is_active:
            self._deactivate_all_libraries()

        library = Library(
            name=name,
            calibre_db_path=calibre_db_path,
            calibre_db_file=calibre_db_file,
            use_split_library=use_split_library,
            split_library_dir=split_library_dir,
            auto_reconnect=auto_reconnect,
            auto_metadata_enforcement=auto_metadata_enforcement,
            is_active=is_active,
        )
        self._library_repo.add(library)
        self._session.flush()
        # If library is created as active, sync any existing shelves (though unlikely)
        if is_active and library.id is not None:
            self._sync_shelves_for_library(library.id, True)
        return library

    def _generate_library_path(self, name: str) -> str:
        """Generate a filesystem-safe path from library name.

        Parameters
        ----------
        name : str
            Library name.

        Returns
        -------
        str
            Generated path in default library directory.

        Raises
        ------
        ValueError
            If name cannot be sanitized or default directory is invalid.
        """
        # Get default library directory
        default_dir = self._get_default_library_directory()

        # Sanitize name: lowercase, replace spaces with hyphens, remove special chars
        sanitized = re.sub(r"[^\w\s-]", "", name.lower())
        sanitized = re.sub(r"[-\s]+", "-", sanitized).strip("-")

        if not sanitized:
            sanitized = "library"

        # Check for conflicts and append number if needed
        base_path = Path(default_dir) / sanitized
        path = base_path
        counter = 1
        while self._library_repo.find_by_path(str(path)) is not None:
            path = Path(default_dir) / f"{sanitized}-{counter}"
            counter += 1

        return path.as_posix()

    @staticmethod
    def _parse_library_path(
        path: str, default_filename: str = "metadata.db"
    ) -> tuple[str, str]:
        """Parse library path to extract directory and filename.

        If the path points to a file, extracts the directory and filename.
        If the path points to a directory, uses the default filename.

        Parameters
        ----------
        path : str
            Library path (can be directory or file).
        default_filename : str
            Default filename to use if path is a directory (default: 'metadata.db').

        Returns
        -------
        tuple[str, str]
            Tuple of (directory_path, filename).
        """
        # Expand user home directory
        path_obj = Path(path).expanduser()
        try:
            # Check if path exists and is a file
            if path_obj.exists() and path_obj.is_file():
                return path_obj.parent.as_posix(), path_obj.name
            # Check if path exists and is a directory
            if path_obj.exists() and path_obj.is_dir():
                return path_obj.as_posix(), default_filename
            # Path doesn't exist - check if it looks like a file (has extension)
            if path_obj.suffix:
                # Assume it's a file path
                return path_obj.parent.as_posix(), path_obj.name
            # Assume it's a directory path
            return path_obj.as_posix(), default_filename
        except (OSError, ValueError):
            # On error, assume it's a directory
            return path_obj.as_posix(), default_filename

    @staticmethod
    def _get_default_library_directory() -> str:
        """Get the default directory for auto-generated libraries.

        Returns
        -------
        str
            Path to default library directory.

        Notes
        -----
        Uses environment variable BOOKCARD_DEFAULT_LIBRARY_DIR if set,
        otherwise defaults to AppConfig's data_directory.
        """
        env_dir = os.getenv("BOOKCARD_DEFAULT_LIBRARY_DIR")
        if env_dir:
            return Path(env_dir).expanduser().as_posix()

        # Default to AppConfig's data_directory
        config = AppConfig.from_env()
        # Normalize to POSIX format for cross-platform compatibility
        return Path(config.data_directory).as_posix()

    def update_library(
        self,
        library_id: int,
        *,
        name: str | None = None,
        calibre_db_path: str | None = None,
        calibre_db_file: str | None = None,
        calibre_uuid: str | None = None,
        use_split_library: bool | None = None,
        split_library_dir: str | None = None,
        auto_reconnect: bool | None = None,
        auto_metadata_enforcement: bool | None = None,
        auto_convert_on_ingest: bool | None = None,
        auto_convert_target_format: str | None = None,
        auto_convert_ignored_formats: str | None = None,
        auto_convert_backup_originals: bool | None = None,
        epub_fixer_auto_fix_on_ingest: bool | None = None,
        duplicate_handling: str | None = None,
        is_active: bool | None = None,
    ) -> Library:
        """Update a library.

        Parameters
        ----------
        library_id : int
            Library identifier.
        name : str | None
            User-friendly library name.
        calibre_db_path : str | None
            Path to Calibre database directory.
        calibre_db_file : str | None
            Calibre database filename.
        calibre_uuid : str | None
            Calibre library UUID.
        use_split_library : bool | None
            Whether to use split library mode.
        split_library_dir : str | None
            Directory for split library mode.
        auto_reconnect : bool | None
            Whether to automatically reconnect on errors.
        auto_convert_on_ingest : bool | None
            Whether to automatically convert books to target format during auto-ingest.
        auto_convert_target_format : str | None
            Target format for automatic conversion during ingest.
        auto_convert_ignored_formats : str | None
            JSON array of format strings to ignore during auto-conversion on ingest.
        auto_convert_backup_originals : bool | None
            Whether to backup original files before conversion during ingest.
        epub_fixer_auto_fix_on_ingest : bool | None
            Whether to automatically fix EPUBs on book upload/ingest.
        duplicate_handling : str | None
            Strategy for handling duplicate books during ingest: IGNORE, OVERWRITE, or CREATE_NEW.
        is_active : bool | None
            Whether to set this as the active library.

        Returns
        -------
        Library
            Updated library.

        Raises
        ------
        ValueError
            If library not found or path conflict.
        """
        library = self._library_repo.get(library_id)
        if library is None:
            msg = "library_not_found"
            raise ValueError(msg)

        self._validate_and_update_path(library, library_id, calibre_db_path)
        self._update_library_fields(
            library,
            name=name,
            calibre_db_file=calibre_db_file,
            calibre_uuid=calibre_uuid,
            use_split_library=use_split_library,
            split_library_dir=split_library_dir,
            auto_reconnect=auto_reconnect,
            auto_metadata_enforcement=auto_metadata_enforcement,
            auto_convert_on_ingest=auto_convert_on_ingest,
            auto_convert_target_format=auto_convert_target_format,
            auto_convert_ignored_formats=auto_convert_ignored_formats,
            auto_convert_backup_originals=auto_convert_backup_originals,
            epub_fixer_auto_fix_on_ingest=epub_fixer_auto_fix_on_ingest,
            duplicate_handling=duplicate_handling,
        )
        self._handle_active_status_change(library, is_active)

        self._session.flush()
        return library

    def _validate_and_update_path(
        self,
        library: Library,
        library_id: int,
        calibre_db_path: str | None,
    ) -> None:
        """Validate and update library path if provided.

        Parameters
        ----------
        library : Library
            Library to update.
        library_id : int
            Library identifier.
        calibre_db_path : str | None
            New path to set.

        Raises
        ------
        ValueError
            If path conflict exists.
        """
        if calibre_db_path is None:
            return

        if calibre_db_path == library.calibre_db_path:
            return

        existing = self._library_repo.find_by_path(calibre_db_path)
        if existing is not None and existing.id != library_id:
            msg = "library_path_already_exists"
            raise ValueError(msg)

        library.calibre_db_path = calibre_db_path

    def _update_library_fields(
        self,
        library: Library,
        *,
        name: str | None = None,
        calibre_db_file: str | None = None,
        calibre_uuid: str | None = None,
        use_split_library: bool | None = None,
        split_library_dir: str | None = None,
        auto_reconnect: bool | None = None,
        auto_metadata_enforcement: bool | None = None,
        auto_convert_on_ingest: bool | None = None,
        auto_convert_target_format: str | None = None,
        auto_convert_ignored_formats: str | None = None,
        auto_convert_backup_originals: bool | None = None,
        epub_fixer_auto_fix_on_ingest: bool | None = None,
        duplicate_handling: str | None = None,
    ) -> None:
        """Update library fields.

        Parameters
        ----------
        library : Library
            Library to update.
        name : str | None
            User-friendly library name.
        calibre_db_file : str | None
            Calibre database filename.
        calibre_uuid : str | None
            Calibre library UUID.
        use_split_library : bool | None
            Whether to use split library mode.
        split_library_dir : str | None
            Directory for split library mode.
        auto_reconnect : bool | None
            Whether to automatically reconnect on errors.
        auto_convert_on_ingest : bool | None
            Whether to automatically convert books to target format during auto-ingest.
        auto_convert_target_format : str | None
            Target format for automatic conversion during ingest.
        auto_convert_ignored_formats : str | None
            JSON array of format strings to ignore during auto-conversion on ingest.
        auto_convert_backup_originals : bool | None
            Whether to backup original files before conversion during ingest.
        epub_fixer_auto_fix_on_ingest : bool | None
            Whether to automatically fix EPUBs on book upload/ingest.
        duplicate_handling : str | None
            Strategy for handling duplicate books during ingest: IGNORE, OVERWRITE, or CREATE_NEW.
        """
        self._update_basic_library_fields(
            library,
            name=name,
            calibre_db_file=calibre_db_file,
            calibre_uuid=calibre_uuid,
            use_split_library=use_split_library,
            split_library_dir=split_library_dir,
            auto_reconnect=auto_reconnect,
            auto_metadata_enforcement=auto_metadata_enforcement,
        )
        self._update_auto_convert_fields(
            library,
            auto_convert_on_ingest=auto_convert_on_ingest,
            auto_convert_target_format=auto_convert_target_format,
            auto_convert_ignored_formats=auto_convert_ignored_formats,
            auto_convert_backup_originals=auto_convert_backup_originals,
            epub_fixer_auto_fix_on_ingest=epub_fixer_auto_fix_on_ingest,
            duplicate_handling=duplicate_handling,
        )

    def _update_basic_library_fields(
        self,
        library: Library,
        *,
        name: str | None = None,
        calibre_db_file: str | None = None,
        calibre_uuid: str | None = None,
        use_split_library: bool | None = None,
        split_library_dir: str | None = None,
        auto_reconnect: bool | None = None,
        auto_metadata_enforcement: bool | None = None,
    ) -> None:
        """Update basic library fields.

        Parameters
        ----------
        library : Library
            Library to update.
        name : str | None
            User-friendly library name.
        calibre_db_file : str | None
            Calibre database filename.
        calibre_uuid : str | None
            Calibre library UUID.
        use_split_library : bool | None
            Whether to use split library mode.
        split_library_dir : str | None
            Directory for split library mode.
        auto_reconnect : bool | None
            Whether to automatically reconnect on errors.
        """
        if name is not None:
            library.name = name
        if calibre_db_file is not None:
            library.calibre_db_file = calibre_db_file
        if calibre_uuid is not None:
            library.calibre_uuid = calibre_uuid
        if use_split_library is not None:
            library.use_split_library = use_split_library
        if split_library_dir is not None:
            library.split_library_dir = split_library_dir
        if auto_reconnect is not None:
            library.auto_reconnect = auto_reconnect
        if auto_metadata_enforcement is not None:
            library.auto_metadata_enforcement = auto_metadata_enforcement
        if auto_metadata_enforcement is not None:
            library.auto_metadata_enforcement = auto_metadata_enforcement

    def _update_auto_convert_fields(
        self,
        library: Library,
        *,
        auto_convert_on_ingest: bool | None = None,
        auto_convert_target_format: str | None = None,
        auto_convert_ignored_formats: str | None = None,
        auto_convert_backup_originals: bool | None = None,
        epub_fixer_auto_fix_on_ingest: bool | None = None,
        duplicate_handling: str | None = None,
    ) -> None:
        """Update auto-convert library fields.

        Parameters
        ----------
        library : Library
            Library to update.
        auto_convert_on_ingest : bool | None
            Whether to automatically convert books to target format during auto-ingest.
        auto_convert_target_format : str | None
            Target format for automatic conversion during ingest.
        auto_convert_ignored_formats : str | None
            JSON array of format strings to ignore during auto-conversion on ingest.
        auto_convert_backup_originals : bool | None
            Whether to backup original files before conversion during ingest.
        epub_fixer_auto_fix_on_ingest : bool | None
            Whether to automatically fix EPUBs on book upload/ingest.
        duplicate_handling : str | None
            Strategy for handling duplicate books during ingest: IGNORE, OVERWRITE, or CREATE_NEW.
        """
        if auto_convert_on_ingest is not None:
            library.auto_convert_on_ingest = auto_convert_on_ingest
        if auto_convert_target_format is not None:
            library.auto_convert_target_format = auto_convert_target_format
        if auto_convert_ignored_formats is not None:
            library.auto_convert_ignored_formats = auto_convert_ignored_formats
        if auto_convert_backup_originals is not None:
            library.auto_convert_backup_originals = auto_convert_backup_originals
        if epub_fixer_auto_fix_on_ingest is not None:
            library.epub_fixer_auto_fix_on_ingest = epub_fixer_auto_fix_on_ingest
        if duplicate_handling is not None:
            library.duplicate_handling = duplicate_handling

    def _handle_active_status_change(
        self,
        library: Library,
        is_active: bool | None,
    ) -> None:
        """Handle active status change for a library.

        Parameters
        ----------
        library : Library
            Library to update.
        is_active : bool | None
            Whether to set this as the active library.
        """
        if is_active is None:
            return

        if is_active and not library.is_active:
            self._deactivate_all_libraries()

        library.is_active = is_active

    def delete_library(self, library_id: int) -> None:
        """Delete a library.

        Parameters
        ----------
        library_id : int
            Library identifier.

        Raises
        ------
        ValueError
            If library not found.
        """
        library = self._library_repo.get(library_id)
        if library is None:
            msg = "library_not_found"
            raise ValueError(msg)

        self._library_repo.delete(library)

    def set_active_library(self, library_id: int) -> Library:
        """Set a library as the active one.

        Parameters
        ----------
        library_id : int
            Library identifier.

        Returns
        -------
        Library
            Updated library.

        Raises
        ------
        ValueError
            If library not found.
        """
        library = self._library_repo.get(library_id)
        if library is None:
            msg = "library_not_found"
            raise ValueError(msg)

        # Deactivate all libraries first
        self._deactivate_all_libraries()

        # Activate the selected library
        library.is_active = True
        # Sync shelf statuses for the newly activated library
        self._sync_shelves_for_library(library_id, True)
        self._session.flush()
        return library

    def get_library_stats(self, library_id: int) -> dict[str, int | float]:
        """Get statistics for a library.

        Parameters
        ----------
        library_id : int
            Library identifier.

        Returns
        -------
        dict[str, int | float]
            Dictionary with library statistics:
            - 'total_books': Total number of books
            - 'total_series': Total number of unique series
            - 'total_authors': Total number of unique authors
            - 'total_content_size': Total file size in bytes

        Raises
        ------
        ValueError
            If library not found.
        FileNotFoundError
            If Calibre database file does not exist.
        """
        library = self._library_repo.get(library_id)
        if library is None:
            msg = "library_not_found"
            raise ValueError(msg)

        book_repo = CalibreBookRepository(
            calibre_db_path=library.calibre_db_path,
            calibre_db_file=library.calibre_db_file,
        )
        return book_repo.get_library_stats()

    def _deactivate_all_libraries(self) -> None:
        """Deactivate all libraries and sync shelf statuses."""
        libraries = self._library_repo.list_all()
        for lib in libraries:
            if lib.is_active:
                lib.is_active = False
                # Sync shelf statuses for this library
                if lib.id is not None:
                    self._sync_shelves_for_library(lib.id, False)
        self._session.flush()

    def _sync_shelves_for_library(
        self,
        library_id: int,
        is_active: bool,
    ) -> None:
        """Sync shelf active status with library active status.

        Parameters
        ----------
        library_id : int
            Library ID whose shelves should be synced.
        is_active : bool
            Active status to set for all shelves in the library.
        """
        shelf_repo = ShelfRepository(self._session)
        shelf_repo.sync_active_status_for_library(library_id, is_active)


class EPUBFixerConfigService:
    """Service for managing EPUB fixer configuration.

    Parameters
    ----------
    session : Session
        Active SQLModel session.
    """

    def __init__(self, session: Session) -> None:  # type: ignore[type-arg]
        """Initialize EPUB fixer config service.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self._session = session

    def get_epub_fixer_config(self) -> EPUBFixerConfig:
        """Get EPUB fixer configuration.

        Returns the existing config or creates a default one if none exists.

        Returns
        -------
        EPUBFixerConfig
            EPUB fixer configuration.
        """
        stmt = select(EPUBFixerConfig).limit(1)
        config = self._session.exec(stmt).first()
        if config is None:
            # Create default config
            config = EPUBFixerConfig()
            self._session.add(config)
            self._session.commit()
            self._session.refresh(config)
        return config

    def update_epub_fixer_config(
        self,
        *,
        enabled: bool | None = None,
        backup_enabled: bool | None = None,
        backup_directory: str | None = None,
        default_language: str | None = None,
        skip_already_fixed: bool | None = None,
        skip_failed: bool | None = None,
    ) -> EPUBFixerConfig:
        """Update EPUB fixer configuration.

        Parameters
        ----------
        enabled : bool | None
            Whether EPUB fixer is enabled.
        backup_enabled : bool | None
            Whether backups are enabled.
        backup_directory : str | None
            Backup directory path.
        default_language : str | None
            Default language for fixes.
        skip_already_fixed : bool | None
            Whether to skip already fixed EPUBs.
        skip_failed : bool | None
            Whether to skip previously failed EPUBs.

        Returns
        -------
        EPUBFixerConfig
            Updated configuration.
        """
        config = self.get_epub_fixer_config()

        if enabled is not None:
            config.enabled = enabled
        if backup_enabled is not None:
            config.backup_enabled = backup_enabled
        if backup_directory is not None:
            config.backup_directory = backup_directory
        if default_language is not None:
            config.default_language = default_language
        if skip_already_fixed is not None:
            config.skip_already_fixed = skip_already_fixed
        if skip_failed is not None:
            config.skip_failed = skip_failed

        self._session.add(config)
        self._session.commit()
        self._session.refresh(config)
        return config

    def is_epub_fixer_enabled(self) -> bool:
        """Check if EPUB fixer is enabled.

        Returns
        -------
        bool
            True if enabled, False otherwise.
        """
        config = self.get_epub_fixer_config()
        return config.enabled

    def is_auto_fix_on_ingest_enabled(self, library: Library | None = None) -> bool:  # type: ignore[name-defined]
        """Check if auto-fix on ingest is enabled for a library.

        Parameters
        ----------
        library : Library | None
            Library to check. If None, uses the active library.

        Returns
        -------
        bool
            True if enabled, False otherwise.
        """
        if library is None:
            # Get active library if not provided
            library_repo = LibraryRepository(self._session)
            library_service = LibraryService(self._session, library_repo)
            library = library_service.get_active_library()

        if library is None:
            return False

        return library.epub_fixer_auto_fix_on_ingest

    def is_daily_scan_enabled(self) -> bool:
        """Check if daily scan is enabled.

        Returns
        -------
        bool
            True if enabled, False otherwise.
        """
        stmt = select(ScheduledTasksConfig).limit(1)
        scheduled_config = self._session.exec(stmt).first()
        if scheduled_config is None:
            return False
        return scheduled_config.epub_fixer_daily_scan


class ScheduledTasksConfigService:
    """Service for managing scheduled tasks configuration.

    Parameters
    ----------
    session : Session
        Active SQLModel session.
    """

    def __init__(self, session: Session) -> None:  # type: ignore[type-arg]
        """Initialize scheduled tasks config service.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self._session = session

    def get_scheduled_tasks_config(self) -> ScheduledTasksConfig:
        """Get scheduled tasks configuration.

        Returns the existing config or creates a default one if none exists.

        Returns
        -------
        ScheduledTasksConfig
            Scheduled tasks configuration.
        """
        stmt = select(ScheduledTasksConfig).limit(1)
        config = self._session.exec(stmt).first()
        if config is None:
            # Create default config
            config = ScheduledTasksConfig()
            self._session.add(config)
            self._session.commit()
            self._session.refresh(config)
        return config

    def register_job(
        self,
        task_type: TaskType,
        cron_expression: str,
        enabled: bool,
        job_name: str,
        arguments: dict | None = None,
    ) -> ScheduledJobDefinition:
        """Register or update a scheduled job.

        Parameters
        ----------
        task_type : TaskType
            Type of task to execute.
        cron_expression : str
            Cron expression for scheduling.
        enabled : bool
            Whether the job is enabled.
        job_name : str
            Unique identifier for the job.
        arguments : dict | None
            Optional arguments for the task.

        Returns
        -------
        ScheduledJobDefinition
            Registered job definition.
        """
        stmt = select(ScheduledJobDefinition).where(
            ScheduledJobDefinition.job_name == job_name
        )
        job = self._session.exec(stmt).first()

        if not job:
            job = ScheduledJobDefinition(
                job_name=job_name,
                task_type=task_type,
                cron_expression=cron_expression,
                enabled=enabled,
                arguments=arguments or {},
            )
            self._session.add(job)
        else:
            job.task_type = task_type
            job.cron_expression = cron_expression
            job.enabled = enabled
            job.arguments = arguments or {}
            self._session.add(job)

        self._session.commit()
        self._session.refresh(job)

        # Notify scheduler of job update via update timestamp or explicit trigger
        # Currently the scheduler polls or relies on application restart/refresh
        # In a real system we might want to signal the scheduler service
        return job

    def unregister_job(self, job_name: str) -> None:
        """Unregister (delete) a scheduled job.

        Parameters
        ----------
        job_name : str
            Unique identifier for the job.
        """
        stmt = select(ScheduledJobDefinition).where(
            ScheduledJobDefinition.job_name == job_name
        )
        job = self._session.exec(stmt).first()

        if job:
            self._session.delete(job)
            self._session.commit()

    def update_scheduled_tasks_config(
        self,
        *,
        start_time_hour: int | None = None,
        duration_hours: int | None = None,
        generate_book_covers: bool | None = None,
        generate_series_covers: bool | None = None,
        reconnect_database: bool | None = None,
        metadata_backup: bool | None = None,
        epub_fixer_daily_scan: bool | None = None,
    ) -> ScheduledTasksConfig:
        """Update scheduled tasks configuration.

        Parameters
        ----------
        start_time_hour : int | None
            Hour of day to start scheduled tasks (0-23).
        duration_hours : int | None
            Maximum duration for scheduled tasks in hours.
        generate_book_covers : bool | None
            Whether to generate book cover thumbnails.
        generate_series_covers : bool | None
            Whether to generate series cover thumbnails.
        reconnect_database : bool | None
            Whether to reconnect to Calibre database.
        metadata_backup : bool | None
            Whether to backup metadata.
        epub_fixer_daily_scan : bool | None
            Whether to enable daily EPUB fixer scan.

        Returns
        -------
        ScheduledTasksConfig
            Updated configuration.
        """
        config = self.get_scheduled_tasks_config()

        if start_time_hour is not None:
            config.start_time_hour = start_time_hour
        if duration_hours is not None:
            config.duration_hours = duration_hours
        if generate_book_covers is not None:
            config.generate_book_covers = generate_book_covers
        if generate_series_covers is not None:
            config.generate_series_covers = generate_series_covers
        if reconnect_database is not None:
            config.reconnect_database = reconnect_database
        if metadata_backup is not None:
            config.metadata_backup = metadata_backup
        if epub_fixer_daily_scan is not None:
            config.epub_fixer_daily_scan = epub_fixer_daily_scan

        self._session.add(config)
        self._session.commit()
        self._session.refresh(config)
        return config


class FileHandlingConfigService:
    """Service for managing file handling configuration.

    Parameters
    ----------
    session : Session
        Active SQLModel session.
    """

    def __init__(self, session: Session) -> None:  # type: ignore[type-arg]
        """Initialize file handling config service.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self._session = session

    def get_file_handling_config(self) -> FileHandlingConfig:
        """Get file handling configuration.

        Returns the existing config or creates a default one if none exists.

        Returns
        -------
        FileHandlingConfig
            File handling configuration.
        """
        stmt = select(FileHandlingConfig).limit(1)
        config = self._session.exec(stmt).first()
        if config is None:
            # Create default config
            config = FileHandlingConfig()
            self._session.add(config)
            self._session.commit()
            self._session.refresh(config)
        return config

    def get_allowed_upload_formats(self) -> list[str]:
        """Get list of allowed upload formats.

        Returns
        -------
        list[str]
            List of allowed file format extensions (without dots).
        """
        config = self.get_file_handling_config()
        if not config.allowed_upload_formats:
            return []
        # Parse comma-separated string and normalize (lowercase, strip whitespace)
        return [
            fmt.strip().lower()
            for fmt in config.allowed_upload_formats.split(",")
            if fmt.strip()
        ]

    def is_format_allowed(self, file_format: str) -> bool:
        """Check if a file format is allowed for upload.

        Parameters
        ----------
        file_format : str
            File format extension (with or without dot).

        Returns
        -------
        bool
            True if format is allowed, False otherwise.
        """
        # Normalize format (remove dot, lowercase)
        normalized = file_format.lower().lstrip(".")
        allowed_formats = self.get_allowed_upload_formats()
        return normalized in allowed_formats
