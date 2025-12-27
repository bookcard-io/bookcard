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
from pathlib import Path

from sqlmodel import Session, select

from bookcard.models.pvr import (
    DownloadItem,
    DownloadItemStatus,
    TrackedBook,
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

        download_path = Path(download_item.file_path)
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

            # Group files (we assume one book per download for now, or take the first group)
            # For multi-file torrents (packs), this might need refinement to handle multiple books
            # But typically a tracked book maps to a single book we want.
            # So we'll take the largest file or the one matching the name best?
            # For now, let's process all discovered files as one group if they are in same dir,
            # or separate groups.
            file_groups = self._file_discovery_service.group_files_by_directory(
                book_files
            )

            if not file_groups:
                logger.warning(
                    "Could not group files for download %d", download_item.id
                )
                self._handle_import_error(download_item, "File grouping failed")
                return

            # Process the primary group (or all groups?)
            # Since DownloadItem links to ONE TrackedBook, we likely expect ONE book.
            # If multiple are found, it might be a pack or extras.
            # We'll pick the most likely candidate (largest file group or similar).
            # For simplicity, we process the first group found.
            target_group = file_groups[0]

            try:
                self._ingest_and_link(target_group, download_item)
            except Exception as e:
                logger.exception("Failed to ingest download %d", download_item.id)
                self._handle_import_error(download_item, f"Ingest failed: {e}")
                return

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

    def _ingest_and_link(
        self, file_group: FileGroup, download_item: DownloadItem
    ) -> None:
        """Ingest the file group and link to tracked book.

        Parameters
        ----------
        file_group : FileGroup
            File group to ingest.
        download_item : DownloadItem
            Download item associated with the files.
        """
        tracked_book = download_item.tracked_book

        # 1. Create ingest history
        history_id = self._ingest_service.process_file_group(file_group)

        # 2. Fetch metadata (optional, we can use tracked book metadata hint)
        # We can pass tracked book title/author as hint
        metadata_hint = {
            "title": tracked_book.title,
            "authors": [tracked_book.author],
        }
        if tracked_book.isbn:
            metadata_hint["isbn"] = tracked_book.isbn

        # Fetch metadata using existing service
        # This will use the hint to find better metadata
        self._ingest_service.fetch_and_store_metadata(history_id, metadata_hint)

        # 3. Add to library
        # We take the first file in group as the main book file
        main_file = file_group.files[0]
        file_format = main_file.suffix.lstrip(".").lower()

        # Get active library ID (where book will be added)
        active_library = self._ingest_service.get_active_library()
        library_id = active_library.id

        book_id = self._ingest_service.add_book_to_library(
            history_id=history_id,
            file_path=main_file,
            file_format=file_format,
            title=tracked_book.title,
            author_name=tracked_book.author,
        )

        # 4. Finalize history
        self._ingest_service.finalize_history(history_id, [book_id])

        # 5. Link to tracked book and update status
        self._update_tracked_book(tracked_book, book_id, library_id, download_item)

        logger.info(
            "Successfully imported download %d as book %d for tracked book %d",
            download_item.id,
            book_id,
            tracked_book.id if tracked_book.id else 0,
        )

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
