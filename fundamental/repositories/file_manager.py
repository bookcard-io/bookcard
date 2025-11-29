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

"""File manager for Calibre library filesystem operations.

This module handles all filesystem operations following SRP.
"""

import logging
import shutil
from io import BytesIO
from pathlib import Path

from PIL import Image
from sqlmodel import Session, select

from fundamental.models.media import Data
from fundamental.repositories.interfaces import IFileManager

logger = logging.getLogger(__name__)


class CalibreFileManager(IFileManager):
    """Manages filesystem operations for Calibre library.

    Handles saving book files, covers, and collecting file paths for deletion.
    Follows SRP by focusing solely on filesystem concerns.
    """

    def save_book_file(
        self,
        file_path: Path,
        library_path: Path,
        book_path_str: str,
        title_dir: str,
        file_format: str,
    ) -> None:
        """Save book file to library directory structure.

        Parameters
        ----------
        file_path : "Path"
            Source file path (temporary location).
        library_path : "Path"
            Library root path.
        book_path_str : str
            Book path string (Author/Title format).
        title_dir : str
            Sanitized title directory name.
        file_format : str
            File format extension.
        """
        book_dir = library_path / book_path_str
        book_dir.mkdir(parents=True, exist_ok=True)
        library_file_path = book_dir / f"{title_dir}.{file_format.lower()}"
        shutil.copy2(file_path, library_file_path)

    def save_book_cover(
        self,
        cover_data: bytes,
        library_path: Path,
        book_path_str: str,
    ) -> bool:
        """Save book cover image to library directory structure.

        Saves cover as cover.jpg in the book's directory. Converts image
        to JPEG format if necessary.

        Parameters
        ----------
        cover_data : bytes
            Cover image data as bytes.
        library_path : Path
            Library root path.
        book_path_str : str
            Book path string (Author/Title format).

        Returns
        -------
        bool
            True if cover was saved successfully, False otherwise.
        """
        try:
            # Load image from bytes
            img = Image.open(BytesIO(cover_data))

            # Convert to RGB if necessary (for JPEG compatibility)
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Save as JPEG
            book_dir = library_path / book_path_str
            book_dir.mkdir(parents=True, exist_ok=True)
            cover_path = book_dir / "cover.jpg"

            # Save with quality 85 (good balance of size and quality)
            img.save(cover_path, format="JPEG", quality=85)
        except (OSError, ValueError, TypeError, AttributeError):
            # If image processing fails, return False
            # This allows the book to be added even if cover extraction fails
            return False
        else:
            return True

    def collect_book_files(
        self,
        session: Session,
        book_id: int,
        book_path: str,
        library_path: Path,
    ) -> tuple[list[Path], Path | None]:
        """Collect filesystem paths for book files before deletion.

        Parameters
        ----------
        session : Session
            Database session for querying Data records.
        book_id : int
            Calibre book ID.
        book_path : str
            Book path string from database.
        library_path : Path
            Library root path.

        Returns
        -------
        tuple[list["Path"], "Path | None"]
            Tuple of (list of file paths to delete, book directory path).
        """
        filesystem_paths: list[Path] = []
        book_dir = library_path / book_path

        if not (book_dir.exists() and book_dir.is_dir()):
            logger.warning(
                "Book directory does not exist or is not a directory: %r",
                book_dir,
            )
            return filesystem_paths, None

        # Find all book files from Data table
        data_stmt = select(Data).where(Data.book == book_id)
        data_records = list(session.exec(data_stmt).all())

        logger.debug("Found %d Data records for book_id=%d", len(data_records), book_id)

        for data_record in data_records:
            file_name = data_record.name or f"{book_id}"
            format_lower = data_record.format.lower()

            # Pattern 1: {name}.{format}
            file_path = book_dir / f"{file_name}.{format_lower}"
            if file_path.exists():
                filesystem_paths.append(file_path)

            # Pattern 2: {book_id}.{format}
            alt_file_path = book_dir / f"{book_id}.{format_lower}"
            if alt_file_path.exists() and alt_file_path not in filesystem_paths:
                filesystem_paths.append(alt_file_path)

        # List all files in directory for fallback matching
        all_files: list[Path] = []
        try:
            all_files = [f for f in book_dir.iterdir() if f.is_file()]
        except OSError as e:
            logger.warning("Failed to list files in book_dir %r: %s", book_dir, e)

        # Fallback: If we didn't find files via Data records, try matching by extension
        # This handles cases where filenames don't match expected patterns
        extension_matched = self._match_files_by_extension(
            all_files, data_records, filesystem_paths, book_id
        )
        filesystem_paths.extend(extension_matched)

        # Add cover.jpg if it exists
        cover_path = book_dir / "cover.jpg"
        if cover_path.exists():
            filesystem_paths.append(cover_path)

        logger.debug(
            "Collected %d filesystem paths for book_id=%d: %s",
            len(filesystem_paths),
            book_id,
            [str(p.name) for p in filesystem_paths],
        )

        return filesystem_paths, book_dir

    def _match_files_by_extension(
        self,
        all_files: list[Path],
        data_records: list[Data],
        existing_paths: list[Path],
        book_id: int,
    ) -> list[Path]:
        """Match files by extension when pattern matching fails.

        Parameters
        ----------
        all_files : list["Path"]
            All files found in the book directory.
        data_records : list[Data]
            Data records from database.
        existing_paths : list["Path"]
            Paths already matched via pattern matching.
        book_id : int
            Book ID for logging.

        Returns
        -------
        list["Path"]
            Additional file paths matched by extension.
        """
        matched_paths: list[Path] = []

        if not data_records:
            if all_files:
                logger.warning(
                    "No Data records found for book_id=%d, but files exist: %s",
                    book_id,
                    [str(f.name) for f in all_files],
                )
            return matched_paths

        # Collect all expected formats from Data records
        expected_formats = {dr.format.lower() for dr in data_records}

        # Match files by extension
        for file_path in all_files:
            file_ext = file_path.suffix.lower().lstrip(".")
            if file_ext in expected_formats and file_path not in existing_paths:
                matched_paths.append(file_path)

        if matched_paths:
            logger.debug(
                "Matched %d files by extension for book_id=%d: %s",
                len(matched_paths),
                book_id,
                [str(p.name) for p in matched_paths],
            )

        return matched_paths

    def move_book_directory(
        self,
        old_book_path: str,
        new_book_path: str,
        library_path: Path,
    ) -> None:
        """Move book directory and all its contents to a new location.

        Moves all files in the book directory including:
        - All book format files (epub, pdf, mobi, etc.)
        - Companion files (cover.jpg, metadata.opf, etc.)
        - Any other files in the directory

        After moving, cleans up empty directories.

        Parameters
        ----------
        old_book_path : str
            Current book path string (Author/Title format).
        new_book_path : str
            New book path string (Author/Title format).
        library_path : Path
            Library root path.

        Raises
        ------
        OSError
            If filesystem operations fail.
        """
        old_dir = library_path / old_book_path
        new_dir = library_path / new_book_path

        # If paths are the same, nothing to do
        if old_dir == new_dir:
            logger.debug("Book path unchanged, skipping move: %s", old_book_path)
            return

        # If old directory doesn't exist, nothing to move
        if not old_dir.exists() or not old_dir.is_dir():
            logger.warning(
                "Old book directory does not exist: %s, creating new directory",
                old_dir,
            )
            new_dir.mkdir(parents=True, exist_ok=True)
            return

        # If new directory already exists and has files, log warning but proceed
        if new_dir.exists() and new_dir.is_dir():
            existing_files = list(new_dir.iterdir())
            if existing_files:
                logger.warning(
                    "New book directory already exists with files: %s, "
                    "files will be moved into it",
                    new_dir,
                )

        # Create new directory structure
        new_dir.mkdir(parents=True, exist_ok=True)

        # Move all files from old directory to new directory
        moved_files = []
        try:
            for item in old_dir.iterdir():
                if item.is_file():
                    new_item_path = new_dir / item.name
                    # If target file exists, log warning but overwrite
                    if new_item_path.exists():
                        logger.warning(
                            "Target file already exists, overwriting: %s", new_item_path
                        )
                    shutil.move(str(item), str(new_item_path))
                    moved_files.append(item.name)
                    logger.debug("Moved file: %s -> %s", item.name, new_item_path)
                elif item.is_dir():
                    # Move subdirectories if any (shouldn't happen in Calibre structure)
                    new_subdir = new_dir / item.name
                    shutil.move(str(item), str(new_subdir))
                    moved_files.append(item.name)
                    logger.debug("Moved subdirectory: %s -> %s", item.name, new_subdir)

            logger.info(
                "Moved %d items from %s to %s",
                len(moved_files),
                old_dir,
                new_dir,
            )
        except (OSError, shutil.Error):
            logger.exception(
                "Failed to move book directory from %s to %s",
                old_dir,
                new_dir,
            )
            raise

        # Clean up empty directories
        self._cleanup_empty_directories(old_dir, library_path)

    def _cleanup_empty_directories(self, book_dir: Path, library_path: Path) -> None:
        """Clean up empty directories after moving book files.

        Removes the book directory and author directory if they are empty,
        working up the directory tree.

        Parameters
        ----------
        book_dir : Path
            Book directory that was moved from.
        library_path : Path
            Library root path (stop cleanup at this level).
        """
        current_dir = book_dir

        # Walk up the directory tree, removing empty directories
        # Stop at library_path to avoid removing the library root
        while current_dir != library_path and current_dir.parent != library_path:
            try:
                # Check if directory is empty
                if current_dir.exists() and current_dir.is_dir():
                    remaining_items = list(current_dir.iterdir())
                    if not remaining_items:
                        current_dir.rmdir()
                        logger.debug("Removed empty directory: %s", current_dir)
                    else:
                        # Directory not empty, stop cleanup
                        logger.debug(
                            "Directory not empty, stopping cleanup: %s (%d items)",
                            current_dir,
                            len(remaining_items),
                        )
                        break
            except OSError as exc:
                logger.warning("Failed to remove directory %s: %s", current_dir, exc)
                # Stop on error to avoid cascading failures
                break

            # Move up one level
            current_dir = current_dir.parent
