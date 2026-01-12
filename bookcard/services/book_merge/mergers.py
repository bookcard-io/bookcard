# Copyright (C) 2026 knguyen and others
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

"""Component mergers for book merge operations."""

import logging
from pathlib import Path

from bookcard.models.core import Book
from bookcard.models.media import Data
from bookcard.services.book_merge.protocols import BookRepository, FileStorage

logger = logging.getLogger(__name__)


class MetadataMerger:
    """Handles metadata merging logic."""

    def __init__(self, repository: BookRepository) -> None:
        self._repository = repository

    def merge(self, keep_book: Book, merge_book: Book) -> bool:
        """Merge metadata from merge_book into keep_book.

        Returns True if keep_book was modified.
        """
        changed = False

        # List of fields to check and fill if empty
        fields = ["publisher", "pubdate", "isbn", "lccn", "series_index"]

        # Simple fields
        for field in fields:
            keep_val = getattr(keep_book, field, None)
            merge_val = getattr(merge_book, field, None)

            # If keep is "empty" (None, empty string, or default/zero where appropriate)
            # and merge has value, update keep
            if not keep_val and merge_val:
                setattr(keep_book, field, merge_val)
                changed = True

        if changed:
            self._repository.save(keep_book)

        return changed


class CoverMerger:
    """Handles cover image merging."""

    def __init__(self, file_storage: FileStorage, library_path: Path) -> None:
        self._file_storage = file_storage
        self._library_path = library_path

    def merge(self, keep_book: Book, merge_book: Book) -> None:
        """Merge cover from merge_book into keep_book if better."""
        if not merge_book.has_cover:
            return

        keep_cover_path = self._get_cover_path(keep_book)
        merge_cover_path = self._get_cover_path(merge_book)

        if not keep_book.has_cover:
            # If keep has no cover but merge does, copy it
            self._file_storage.copy_file(merge_cover_path, keep_cover_path)
            keep_book.has_cover = True
            return

        # Both have covers, compare quality
        if not self._file_storage.exists(
            keep_cover_path
        ) or not self._file_storage.exists(merge_cover_path):
            return

        try:
            keep_quality = self._file_storage.get_image_quality(keep_cover_path)
            merge_quality = self._file_storage.get_image_quality(merge_cover_path)

            # Heuristic: Prefer larger area (width * height), then larger file size
            keep_score = keep_quality["area"]
            merge_score = merge_quality["area"]

            if merge_score > keep_score:
                logger.info(
                    "Replacing cover for book %s with better cover from %s",
                    keep_book.id,
                    merge_book.id,
                )
                self._file_storage.copy_file(merge_cover_path, keep_cover_path)
            elif (
                merge_score == keep_score
                and merge_quality["size"] > keep_quality["size"]
            ):
                logger.info(
                    "Replacing cover for book %s with larger file from %s",
                    keep_book.id,
                    merge_book.id,
                )
                self._file_storage.copy_file(merge_cover_path, keep_cover_path)

        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to compare covers: %s", e)

    def _get_cover_path(self, book: Book) -> Path:
        """Get path to cover.jpg."""
        return self._library_path / book.path / "cover.jpg"


class FileMerger:
    """Handles file merging and conflict resolution."""

    def __init__(
        self, file_storage: FileStorage, repository: BookRepository, library_path: Path
    ) -> None:
        self._file_storage = file_storage
        self._repository = repository
        self._library_path = library_path

    def merge(
        self,
        keep_book: Book,
        merge_book: Book,
        keep_data: list[Data],
        merge_data: list[Data],
    ) -> None:
        """Merge files from merge_book to keep_book."""
        keep_formats = {d.format.upper(): d for d in keep_data}

        keep_dir = self._library_path / keep_book.path
        merge_dir = self._library_path / merge_book.path

        for data in merge_data:
            fmt = data.format.upper()

            # Resolve source file
            src_file = self._file_storage.find_file(merge_dir, data.name, data.format)

            if not src_file:
                expected = merge_dir / self._construct_filename(data.name, data.format)
                logger.warning(
                    "File missing for book %s: %s (and variations)",
                    merge_book.id,
                    expected,
                )
                continue

            if fmt in keep_formats:
                self._handle_conflict(
                    data, keep_formats[fmt], src_file, keep_dir, keep_book, merge_book
                )
            else:
                self._move_and_link(data, src_file, keep_dir, keep_book)

    def _handle_conflict(
        self,
        merge_data_record: Data,
        keep_data_record: Data,
        src_file: Path,
        keep_dir: Path,
        keep_book: Book,
        merge_book: Book,
    ) -> None:
        """Handle file conflict."""
        # Try to find existing file to handle case-sensitivity
        keep_file = self._file_storage.find_file(
            keep_dir, keep_data_record.name, keep_data_record.format
        )
        if not keep_file:
            # Fallback to constructed path
            keep_file = keep_dir / self._construct_filename(
                keep_data_record.name, keep_data_record.format
            )

        src_size = merge_data_record.uncompressed_size
        keep_size = keep_data_record.uncompressed_size

        if src_size > keep_size:
            # Replace keep with src
            logger.info(
                "Replacing %s for book %s with larger file from %s",
                keep_data_record.format,
                keep_book.id,
                merge_book.id,
            )

            # Backup keep
            self._file_storage.backup_file(keep_file)

            # Move src to keep location
            self._file_storage.move_file(src_file, keep_file)

            # Update DB record for keep_book
            keep_data_record.uncompressed_size = src_size
            self._repository.save(keep_data_record)

        else:
            # Keep is better (or equal), just move src as backup
            logger.info(
                "Keeping existing %s for book %s, backing up merged file",
                keep_data_record.format,
                keep_book.id,
            )

            dest_bak = self._file_storage.get_unique_bak_path(keep_file)
            self._file_storage.move_file(src_file, dest_bak)

    def _move_and_link(
        self, data: Data, src_file: Path, keep_dir: Path, keep_book: Book
    ) -> None:
        """Move file and update data record."""
        dest_file = keep_dir / self._construct_filename(data.name, data.format)

        # Handle filename collision if file exists but not in DB
        if self._file_storage.exists(dest_file):
            stem = dest_file.stem
            suffix = dest_file.suffix
            counter = 1
            while self._file_storage.exists(dest_file):
                dest_file = keep_dir / f"{stem}_{counter}{suffix}"
                counter += 1

        self._file_storage.move_file(src_file, dest_file)

        # Update Data record to point to keep_book
        data.book = keep_book.id
        data.name = dest_file.stem
        self._repository.save(data)

    def _construct_filename(self, name: str, fmt: str) -> str:
        """Construct filename with lowercase extension."""
        return f"{name}.{fmt.lower()}"


class CleanupService:
    """Handles cleanup after merge."""

    def __init__(
        self, repository: BookRepository, file_storage: FileStorage, library_path: Path
    ) -> None:
        self._repository = repository
        self._file_storage = file_storage
        self._library_path = library_path

    def cleanup(self, merge_book: Book) -> None:
        """Clean up merged book records and files."""
        # Delete any remaining data records (e.g. backed up files)
        # Note: In _move_and_link, data records are updated to new book.
        # In _handle_conflict, keep data record is updated, merge data record remains pointing to old book?
        # Actually in _handle_conflict, we didn't touch merge_data_record in DB, we just moved the file.
        # So we should delete all remaining data records for merge_book.

        # Note: The merge_books function in service gets data BEFORE passing to merger.
        # But we need to query fresh or assume remaining are to be deleted.
        # We can just query by merge_book.id

        if not merge_book.id:
            # Should not happen for persisted book
            return

        result = self._repository.get_with_data(merge_book.id)
        if result:
            _, remaining_data = result
            for d in remaining_data:
                self._repository.delete_data(d)

        # Delete directory
        merge_dir = self._library_path / merge_book.path
        self._file_storage.delete_directory(merge_dir)

        # Delete Book record
        self._repository.delete(merge_book)
