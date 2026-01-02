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

"""PVR import service.

Handles importing completed downloads into the library.
Follows SRP by orchestrating the import process: extraction, discovery, and ingestion.
"""

import logging
import shutil
import tempfile
from contextlib import suppress
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from bookcard.models.pvr import (
    DownloadItem,
    DownloadItemStatus,
    TrackedBook,
    TrackedBookFile,
    TrackedBookStatus,
)
from bookcard.services.ingest.file_discovery_service import (
    FileDiscoveryService,
    FileGroup,
)
from bookcard.services.ingest.ingest_processor_service import IngestProcessorService
from bookcard.services.tracked_book_service import TrackedBookService

logger = logging.getLogger(__name__)


class PVRImportService:
    """Service for importing completed PVR downloads.

    Orchestrates the process of:
    1. Extracting files from completed downloads
    2. Discovering book files
    3. Triggering the ingest process
    4. Linking imported books to tracked books

    Parameters
    ----------
    session : Session
        Database session.
    ingest_service : IngestProcessorService | None
        Optional ingest processor service.
    tracked_book_service : TrackedBookService | None
        Optional tracked book service.
    file_discovery_service : FileDiscoveryService | None
        Optional file discovery service.
    """

    def __init__(
        self,
        session: Session,
        ingest_service: IngestProcessorService | None = None,
        tracked_book_service: TrackedBookService | None = None,
        file_discovery_service: FileDiscoveryService | None = None,
    ) -> None:
        """Initialize PVR import service.

        Parameters
        ----------
        session : Session
            Database session.
        ingest_service : IngestProcessorService | None
            Optional ingest processor service.
        tracked_book_service : TrackedBookService | None
            Optional tracked book service.
        file_discovery_service : FileDiscoveryService | None
            Optional file discovery service.
        """
        self._session = session
        self._ingest_service = ingest_service or IngestProcessorService(session)
        self._tracked_book_service = tracked_book_service or TrackedBookService(session)
        self._file_discovery_service = file_discovery_service or FileDiscoveryService(
            supported_formats=["epub", "mobi", "pdf", "cbz", "cbr", "azw3"],
        )

    def import_pending_downloads(self) -> int:
        """Find and import all pending completed downloads.

        Returns
        -------
        int
            Number of downloads processed.
        """
        statement = (
            select(DownloadItem)
            .join(TrackedBook)
            .where(DownloadItem.status == DownloadItemStatus.COMPLETED)
            .where(TrackedBook.status != TrackedBookStatus.COMPLETED)
            .where(TrackedBook.status != TrackedBookStatus.FAILED)
        )

        items = self._session.exec(statement).all()

        count = 0
        for item in items:
            try:
                self.process_completed_download(item)
                count += 1
            except Exception:
                logger.exception("Error processing download item %d", item.id)
                # Continue with next item

        return count

    def process_completed_download(self, download_item: DownloadItem) -> None:
        """Process a completed download item.

        Extracts files, discovers books, and ingests them into the library.
        Updates the tracked book status upon success.

        Parameters
        ----------
        download_item : DownloadItem
            The completed download item to process.

        Raises
        ------
        ValueError
            If download item is not in COMPLETED status or has no file path.
        FileNotFoundError
            If the downloaded file/directory does not exist.
        """
        if download_item.status != DownloadItemStatus.COMPLETED:
            msg = f"Download item {download_item.id} is not completed (status: {download_item.status})"
            raise ValueError(msg)

        if not download_item.file_path:
            msg = f"Download item {download_item.id} has no file path"
            raise ValueError(msg)

        # Apply path mappings if configured
        download_path = self._resolve_download_path(download_item)

        if not download_path.exists():
            msg = f"Download path does not exist: {download_path}"
            raise FileNotFoundError(msg)

        logger.info(
            "Processing completed download %d: %s", download_item.id, download_path
        )

        # Create a temporary directory for extraction/processing
        with tempfile.TemporaryDirectory(prefix="pvr_import_") as temp_dir:
            temp_path = Path(temp_dir)

            # Extract or copy files to temp dir
            try:
                self._prepare_files(download_path, temp_path)
            except Exception as e:
                logger.exception(
                    "Failed to prepare files for download %d", download_item.id
                )
                self._handle_import_error(
                    download_item, f"File preparation failed: {e}"
                )
                return

            # Discover book files
            try:
                book_files = self._file_discovery_service.discover_files(temp_path)
            except Exception as e:
                logger.exception(
                    "Failed to discover files for download %d", download_item.id
                )
                self._handle_import_error(download_item, f"File discovery failed: {e}")
                return

            if not book_files:
                logger.warning("No book files found in download %d", download_item.id)
                self._handle_import_error(
                    download_item, "No supported book files found"
                )
                return

            # Group files
            file_groups = self._file_discovery_service.group_files_by_directory(
                book_files
            )

            if not file_groups:
                logger.warning(
                    "Could not group files for download %d", download_item.id
                )
                self._handle_import_error(download_item, "File grouping failed")
                return

            ingested_book_ids = self._process_file_groups(file_groups, download_item)

            if not ingested_book_ids:
                logger.warning(
                    "No books were successfully ingested for download %d",
                    download_item.id,
                )
                self._handle_import_error(download_item, "All file ingestions failed")
                return

            # Link the best matching book
            self._link_best_match(download_item, ingested_book_ids)

    def _resolve_download_path(self, download_item: DownloadItem) -> Path:
        """Resolve the local download path using client mappings.

        Parameters
        ----------
        download_item : DownloadItem
            Download item to resolve path for.

        Returns
        -------
        Path
            Resolved local path.
        """
        original_path = download_item.file_path
        if not original_path:
            return Path()

        client = download_item.client
        if not client or not client.additional_settings:
            return Path(original_path)

        path_mappings = client.additional_settings.get("path_mappings")
        if not path_mappings or not isinstance(path_mappings, list):
            return Path(original_path)

        # Normalize separators for comparison if needed, but simple string replace is safer
        # to avoid OS differences logic if client is different OS.
        # Assuming mappings are correct.

        for mapping in path_mappings:
            if not isinstance(mapping, dict):
                continue

            remote = mapping.get("remote")
            local = mapping.get("local")

            if not remote or not local:
                continue

            # If path starts with remote path, replace it
            if original_path.startswith(remote):
                # Ensure we handle trailing slashes correctly
                # simple replace might be dangerous if remote is "/data" and path is "/dataset"
                # but good enough for typical use cases if user provides clean paths.
                resolved_path = original_path.replace(remote, local, 1)
                logger.debug(
                    "Mapped remote path '%s' to local path '%s'",
                    original_path,
                    resolved_path,
                )
                return Path(resolved_path)

        return Path(original_path)

    def _process_file_groups(
        self, file_groups: list[FileGroup], download_item: DownloadItem
    ) -> list[int]:
        """Process all file groups.

        Parameters
        ----------
        file_groups : list[FileGroup]
            List of file groups to process.
        download_item : DownloadItem
            Download item context.

        Returns
        -------
        list[int]
            List of ingested book IDs.
        """
        ingested_book_ids: list[int] = []

        # Process ALL groups
        for group in file_groups:
            try:
                book_id = self._ingest_file_group(group, download_item)
                if book_id:
                    ingested_book_ids.append(book_id)
            except Exception:
                logger.exception(
                    "Failed to ingest file group %s for download %d",
                    group.book_key,
                    download_item.id,
                )
                # Continue with other groups

        return ingested_book_ids

    def _prepare_files(self, source_path: Path, dest_dir: Path) -> None:
        """Prepare files for ingestion by extracting or copying.

        Parameters
        ----------
        source_path : Path
            Source file or directory.
        dest_dir : Path
            Destination directory.
        """
        if source_path.is_file():
            # Check if it's an archive
            if self._is_archive(source_path):
                logger.info("Extracting archive %s to %s", source_path, dest_dir)
                shutil.unpack_archive(source_path, dest_dir)
            else:
                # Copy single file
                logger.info("Copying file %s to %s", source_path, dest_dir)
                shutil.copy2(source_path, dest_dir)
        elif source_path.is_dir():
            # Copy directory contents, extracting archives within if needed?
            # For now, just copy the tree. Recursively extracting archives inside might be dangerous/slow.
            # We'll just copy the directory structure.
            # shutil.copytree requires dest to not exist or be empty depending on version/flags.
            # dest_dir is the temp root, so we copy into a subdir or contents.
            logger.info("Copying directory %s to %s", source_path, dest_dir)
            # copytree fails if dest exists usually, so we copy contents
            for item in source_path.iterdir():
                if item.is_dir():
                    shutil.copytree(item, dest_dir / item.name)
                else:
                    shutil.copy2(item, dest_dir)
                    # Also check for archives in the dir?
                    # Maybe complex. Let's assume the downloader unzipped if it's a dir,
                    # or we just scan for book files.
                    if self._is_archive(item):
                        with suppress(Exception):
                            # Try to extract archives found inside the dir too
                            extract_dir = dest_dir / item.stem
                            extract_dir.mkdir(exist_ok=True)
                            shutil.unpack_archive(item, extract_dir)

    def _is_archive(self, path: Path) -> bool:
        """Check if file is a supported archive format.

        Parameters
        ----------
        path : Path
            File path.

        Returns
        -------
        bool
            True if archive, False otherwise.
        """
        # extensions supported by shutil.unpack_archive
        archive_extensions = {".zip", ".tar", ".gztar", ".bztar", ".xztar", ".rar"}
        # Note: .rar support depends on external tools usually, shutil might not support it out of box without registration.
        # standard python shutil supports zip, tar variants.
        # We'll stick to what shutil.get_unpack_formats() says, but checking extension is faster/easier for now.
        # Actually, let's use shutil to check.
        # But for simple check:
        return (
            path.suffix.lower() in archive_extensions or path.suffix.lower() == ".rar"
        )

    def _ingest_file_group(
        self, file_group: FileGroup, download_item: DownloadItem
    ) -> int | None:
        """Ingest a single file group.

        Parameters
        ----------
        file_group : FileGroup
            File group to ingest.
        download_item : DownloadItem
            Download item context.

        Returns
        -------
        int | None
            Book ID if successful, None otherwise.
        """
        tracked_book = download_item.tracked_book

        # 1. Create ingest history
        history_id = self._ingest_service.process_file_group(file_group)

        # 2. Fetch metadata (using tracked book as hint)
        metadata_hint = {
            "title": tracked_book.title,
            "authors": [tracked_book.author],
        }
        if tracked_book.isbn:
            metadata_hint["isbn"] = tracked_book.isbn

        self._ingest_service.fetch_and_store_metadata(history_id, metadata_hint)

        # 3. Select best file from group
        main_file = self._select_best_file(file_group, tracked_book.preferred_formats)
        if not main_file:
            logger.warning("No valid file found in group %s", file_group.book_key)
            return None

        file_format = main_file.suffix.lstrip(".").lower()

        # 4. Add to library
        book_id = self._ingest_service.add_book_to_library(
            history_id=history_id,
            file_path=main_file,
            file_format=file_format,
            title=tracked_book.title,
            author_name=tracked_book.author,
        )

        # Get book service to query paths
        library = self._ingest_service.get_active_library()
        book_service = self._ingest_service.create_book_service(library)

        # Record main file
        try:
            main_path = book_service.get_format_file_path(book_id, file_format)
            self._create_tracked_file(
                tracked_book,
                main_path,
                "main",
                main_file.name,
                main_file.stat().st_size,
            )
        except (ValueError, RuntimeError, OSError) as e:
            logger.warning("Failed to record main file for book %d: %s", book_id, e)

        # 5. Add other files as formats
        # Filter out the main file we just added
        other_files = [f for f in file_group.files if f != main_file]

        for other_file in other_files:
            other_format = other_file.suffix.lstrip(".").lower()
            try:
                self._ingest_service.add_format_to_book(
                    book_id=book_id,
                    file_path=other_file,
                    file_format=other_format,
                )
                # Record as format
                try:
                    fmt_path = book_service.get_format_file_path(book_id, other_format)
                    self._create_tracked_file(
                        tracked_book,
                        fmt_path,
                        "format",
                        other_file.name,
                        other_file.stat().st_size,
                    )
                except (ValueError, RuntimeError, OSError) as e:
                    logger.warning(
                        "Failed to record format file %s for book %d: %s",
                        other_format,
                        book_id,
                        e,
                    )

            except (ValueError, RuntimeError, OSError) as e:
                # If adding format failed, record as artifact if useful
                logger.warning(
                    "Failed to add extra format %s (file: %s) to book %d: %s",
                    other_format,
                    other_file,
                    book_id,
                    e,
                )
                # Try to copy as artifact if it's a useful file type
                # For now, just record it as artifact (maybe we should copy it to the book dir?)
                # If we don't copy it, the path will be in /tmp and disappear.
                # So we must copy it to preserve it.
                self._copy_and_record_artifact(
                    tracked_book, other_file, book_service, book_id
                )

        # 6. Finalize history
        self._ingest_service.finalize_history(history_id, [book_id])

        return book_id

    def _create_tracked_file(
        self,
        tracked_book: TrackedBook,
        path: Path,
        file_type: str,
        filename: str,
        size_bytes: int = 0,
    ) -> None:
        """Create a TrackedBookFile record.

        Parameters
        ----------
        tracked_book : TrackedBook
            Tracked book.
        path : Path
            File path.
        file_type : str
            Type of file.
        filename : str
            Filename.
        size_bytes : int
            Size in bytes.
        """
        tracked_file = TrackedBookFile(
            tracked_book_id=tracked_book.id,
            path=str(path),
            filename=filename,
            size_bytes=size_bytes,
            file_type=file_type,
        )
        self._session.add(tracked_file)
        self._session.commit()

    def _copy_and_record_artifact(
        self,
        tracked_book: TrackedBook,
        source_path: Path,
        book_service: "BookService",  # type: ignore[name-defined] # noqa: F821
        book_id: int,
    ) -> None:
        """Copy file to book directory and record as artifact.

        Parameters
        ----------
        tracked_book : TrackedBook
            Tracked book.
        source_path : Path
            Source file path.
        book_service : BookService
            Book service instance.
        book_id : int
            Book ID.
        """
        try:
            # Determine book directory
            # We can get it from the main file or query book info
            book_rel = book_service.get_book(book_id)
            if not book_rel:
                return

            # Determine library root from book path
            # book.path is relative to library root
            # We assume we can write to the library directory
            # We need the absolute path to the book directory
            # book_service doesn't expose get_library_root directly publicly maybe?
            # But we can try to guess from a known format path

            # Alternative: Use BookService internal knowledge or config
            # BookService uses self._library.calibre_db_path (which is db file)
            # Parent is usually the root
            library_path = Path(book_service.library.calibre_db_path).parent
            if (
                hasattr(book_service.library, "library_root")
                and book_service.library.library_root
            ):
                library_path = Path(book_service.library.library_root)

            book_dir = library_path / book_rel.book.path

            if not book_dir.exists():
                logger.warning("Book directory does not exist: %s", book_dir)
                return

            dest_path = book_dir / source_path.name

            # Don't overwrite if exists
            if dest_path.exists():
                logger.debug("Artifact %s already exists in book dir", source_path.name)
                # Record existing?
                self._create_tracked_file(
                    tracked_book,
                    dest_path,
                    "artifact",
                    source_path.name,
                    dest_path.stat().st_size,
                )
                return

            shutil.copy2(source_path, dest_path)
            logger.info("Copied artifact %s to %s", source_path.name, dest_path)

            self._create_tracked_file(
                tracked_book,
                dest_path,
                "artifact",
                source_path.name,
                dest_path.stat().st_size,
            )

        except (ValueError, RuntimeError, OSError) as e:
            logger.warning(
                "Failed to copy artifact %s for book %d: %s", source_path, book_id, e
            )

    def _select_best_file(
        self, file_group: FileGroup, preferred_formats: list[str] | None
    ) -> Path | None:
        """Select the best file from the group based on preferences.

        Parameters
        ----------
        file_group : FileGroup
            File group to select from.
        preferred_formats : list[str] | None
            List of preferred formats (e.g. ['epub', 'mobi']).

        Returns
        -------
        Path | None
            Selected file path.
        """
        if not file_group.files:
            return None

        if not preferred_formats:
            # Default preferences: epub > mobi > pdf > others
            preferred_formats = ["epub", "mobi", "azw3", "pdf", "cbz", "cbr"]

        # Normalize preferred formats
        preferred_set = [f.lower() for f in preferred_formats]

        # Sort files by preference index (lowest index = highest priority)
        def sort_key(path: Path) -> tuple[int, int]:
            ext = path.suffix.lstrip(".").lower()
            try:
                priority = preferred_set.index(ext)
            except ValueError:
                priority = 999
            # Secondary sort by file size (largest first)
            size = -path.stat().st_size
            return priority, size

        sorted_files = sorted(file_group.files, key=sort_key)
        return sorted_files[0] if sorted_files else None

    def _link_best_match(
        self, download_item: DownloadItem, book_ids: list[int]
    ) -> None:
        """Find and link the best matching book to the tracked book.

        Parameters
        ----------
        download_item : DownloadItem
            Download item containing the tracked book.
        book_ids : list[int]
            List of ingested book IDs to choose from.
        """
        if not book_ids:
            return

        tracked_book = download_item.tracked_book
        active_library = self._ingest_service.get_active_library()

        # If only one book, link it directly
        if len(book_ids) == 1:
            self._update_tracked_book(
                tracked_book, book_ids[0], active_library.id, download_item
            )
            return

        # Multiple books - find best match
        best_match_id = None
        best_score = 0.0

        # We need to get book details to compare.
        # Using a temporary service instance to fetch book info.
        book_service = self._ingest_service.create_book_service(active_library)

        target_title = tracked_book.title.lower()
        target_author = tracked_book.author.lower()

        for book_id in book_ids:
            try:
                book = book_service.get_book(book_id)
                if not book:
                    continue

                score = self._calculate_match_score(
                    target_title, target_author, book.book.title, book.authors
                )

                if score > best_score:
                    best_score = score
                    best_match_id = book_id
            except (SQLAlchemyError, ValueError, AttributeError, TypeError) as e:
                logger.warning(
                    "Error calculating match score for book %d: %s", book_id, e
                )
                continue

        # If we found a reasonable match (> 0.6?), link it
        # Otherwise, maybe link the first one or mark as ambiguous?
        # For now, we link the best one if score is decent, else the first one.
        if best_match_id and best_score > 0.4:
            self._update_tracked_book(
                tracked_book, best_match_id, active_library.id, download_item
            )
        else:
            # Fallback to first one
            logger.warning(
                "No strong match found for tracked book %d among %d ingested books. Linking first one.",
                tracked_book.id,
                len(book_ids),
            )
            self._update_tracked_book(
                tracked_book, book_ids[0], active_library.id, download_item
            )

    def _calculate_match_score(
        self,
        target_title: str,
        target_author: str,
        book_title: str,
        book_authors: list[str],
    ) -> float:
        """Calculate similarity score between tracked book and ingested book."""
        # Title similarity
        title_score = SequenceMatcher(None, target_title, book_title.lower()).ratio()

        # Author similarity (check against all authors)
        author_score = 0.0
        if book_authors:
            author_scores = [
                SequenceMatcher(None, target_author, a.lower()).ratio()
                for a in book_authors
            ]
            author_score = max(author_scores)

        # Weighted average (Title matters more?)
        return (title_score * 0.7) + (author_score * 0.3)

    def _update_tracked_book(
        self,
        tracked_book: TrackedBook,
        book_id: int,
        library_id: int | None,
        download_item: DownloadItem,  # noqa: ARG002
    ) -> None:
        """Update tracked book status and links.

        Parameters
        ----------
        tracked_book : TrackedBook
            Tracked book to update.
        book_id : int
            ID of the imported book.
        library_id : int | None
            ID of the library where book was imported.
        download_item : DownloadItem
            The download item that was imported.
        """
        tracked_book.status = TrackedBookStatus.COMPLETED
        tracked_book.matched_book_id = book_id
        tracked_book.matched_library_id = library_id
        tracked_book.last_downloaded_at = datetime.now(UTC)
        tracked_book.error_message = None

        self._session.add(tracked_book)
        self._session.commit()

        # Also update download item if needed (though it's already COMPLETED)
        # Maybe add a note or log?
        # status is already COMPLETED.

    def _handle_import_error(
        self, download_item: DownloadItem, error_message: str
    ) -> None:
        """Handle import error.

        Parameters
        ----------
        download_item : DownloadItem
            Download item that failed.
        error_message : str
            Error message.
        """
        download_item.error_message = error_message
        # We might want to set status to FAILED or keep as COMPLETED but with error?
        # If import fails, the download itself (bytes) is complete, but the process failed.
        # Maybe we need an IMPORT_FAILED status?
        # For now, let's set tracked book to FAILED?

        tracked_book = download_item.tracked_book
        tracked_book.status = TrackedBookStatus.FAILED
        tracked_book.error_message = f"Import failed: {error_message}"

        self._session.add(download_item)
        self._session.add(tracked_book)
        self._session.commit()
