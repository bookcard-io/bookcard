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

"""OpenLibrary dump ingestion task implementation.

Ingests OpenLibrary dump files into PostgreSQL database for fast lookups
during library scanning.
"""

import gzip
import json
import logging
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlmodel import Session

from fundamental.models.openlibrary import (
    OpenLibraryAuthor,
    OpenLibraryAuthorWork,
    OpenLibraryEdition,
    OpenLibraryEditionIsbn,
    OpenLibraryWork,
)
from fundamental.services.tasks.base import BaseTask

logger = logging.getLogger(__name__)


class OpenLibraryDumpIngestTask(BaseTask):
    """Task for ingesting OpenLibrary dump files into PostgreSQL DB.

    Reads compressed dump files and populates PostgreSQL database tables
    optimized for read performance with proper indexes.
    """

    def __init__(
        self,
        task_id: int,
        user_id: int,
        metadata: dict[str, Any],
    ) -> None:
        """Initialize OpenLibrary dump ingest task.

        Parameters
        ----------
        task_id : int
            Database task ID.
        user_id : int
            User ID creating the task.
        metadata : dict[str, Any]
            Task metadata. Can contain 'data_directory', 'process_authors',
            'process_works', 'process_editions'.
        """
        super().__init__(task_id, user_id, metadata)
        data_directory = metadata.get("data_directory", "/data")
        self.base_dir = Path(data_directory) / "openlibrary"
        self.dump_dir = self.base_dir / "dump"
        self.batch_size = 10000
        self.process_authors = metadata.get("process_authors", True)
        self.process_works = metadata.get("process_works", True)
        self.process_editions = metadata.get("process_editions", True)

    def _parse_line(
        self, line: str
    ) -> tuple[str, str, int | None, date | None, dict[str, Any]] | None:
        r"""Parse a single line from dump file.

        Format: type\tkey\trevision\tlast_modified\tjson

        Parameters
        ----------
        line : str
            Line from dump file.

        Returns
        -------
        tuple[str, str, int | None, date | None, dict[str, Any]] | None
            Tuple of (type, key, revision, last_modified, data) or None if invalid.
        """
        parts = line.split("\t")
        if len(parts) < 5:
            return None

        try:
            record_type = parts[0]
            key = parts[1]
            revision_str = parts[2]
            last_modified_str = parts[3]
            json_str = parts[4]

            # Parse revision
            revision = int(revision_str) if revision_str else None

            # Parse last_modified date
            last_modified = None
            if last_modified_str:
                try:
                    # OpenLibrary uses ISO format: 2008-04-01T00:00:00
                    dt = datetime.fromisoformat(
                        last_modified_str.replace("Z", "+00:00")
                    )
                    last_modified = dt.date()
                except (ValueError, AttributeError):
                    pass

            # Parse JSON data
            data = json.loads(json_str)
        except (json.JSONDecodeError, ValueError, IndexError):
            return None
        else:
            return (record_type, key, revision, last_modified, data)

    def _process_authors_file(
        self,
        file_path: Path,
        session: Session,
        update_progress: Callable[[float, dict[str, Any] | None], None],
        progress_offset: float,
        progress_scale: float,
    ) -> int:
        """Process authors dump file.

        Parameters
        ----------
        file_path : Path
            Path to authors dump file.
        session : Session
            Database session.
        update_progress : Callable
            Progress update callback.
        progress_offset : float
            Starting progress value (0.0-1.0).
        progress_scale : float
            Scale factor for this file's progress.

        Returns
        -------
        int
            Number of records processed.
        """
        logger.info("Processing authors file: %s", file_path.name)

        if not file_path.exists():
            logger.warning("File not found: %s", file_path)
            return 0

        processed_count = 0
        batch = []

        def _raise_cancelled() -> None:
            """Raise InterruptedError for cancelled task."""
            msg = "Task cancelled"
            raise InterruptedError(msg)

        try:
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                for line in f:
                    if self.check_cancelled():
                        _raise_cancelled()

                    parsed = self._parse_line(line)
                    if parsed is None:
                        continue

                    record_type, key, revision, last_modified, data = parsed

                    # Only process author records
                    if not key.startswith("/authors/"):
                        continue

                    author = OpenLibraryAuthor(
                        type=record_type,
                        key=key,
                        revision=revision,
                        last_modified=last_modified,
                        data=data,
                    )
                    batch.append(author)
                    processed_count += 1

                    if len(batch) >= self.batch_size:
                        session.bulk_save_objects(batch)
                        session.commit()
                        batch = []
                        self._update_progress_if_needed(
                            processed_count,
                            progress_offset,
                            progress_scale,
                            file_path.name,
                            "authors",
                            update_progress,
                        )

                # Insert remaining
                if batch:
                    session.bulk_save_objects(batch)
                    session.commit()

        except Exception:
            logger.exception("Error processing authors file %s", file_path)
            session.rollback()
            raise

        return processed_count

    def _extract_author_works(
        self, data: dict[str, Any], work_key: str
    ) -> list[OpenLibraryAuthorWork]:
        """Extract author-works relationships from work data.

        Deduplicates author-work pairs to prevent unique constraint violations.
        A work may have duplicate author entries in the source data.

        Parameters
        ----------
        data : dict[str, Any]
            Work data dictionary.
        work_key : str
            Work key identifier.

        Returns
        -------
        list[OpenLibraryAuthorWork]
            List of unique author-work relationships.
        """
        author_works = []
        seen_pairs: set[tuple[str, str]] = set()
        authors = data.get("authors", [])
        if isinstance(authors, list):
            for author_ref in authors:
                if isinstance(author_ref, dict):
                    author_key = author_ref.get("author", {}).get("key")
                    if author_key and isinstance(author_key, str):
                        pair = (author_key, work_key)
                        if pair not in seen_pairs:
                            seen_pairs.add(pair)
                            author_works.append(
                                OpenLibraryAuthorWork(
                                    author_key=author_key, work_key=work_key
                                )
                            )
        return author_works

    def _deduplicate_author_works_batch(
        self, batch: list[OpenLibraryAuthorWork]
    ) -> list[OpenLibraryAuthorWork]:
        """Deduplicate author-work batch by composite key.

        Parameters
        ----------
        batch : list[OpenLibraryAuthorWork]
            Batch of author-work relationships.

        Returns
        -------
        list[OpenLibraryAuthorWork]
            Deduplicated batch.
        """
        seen: set[tuple[str, str]] = set()
        unique: list[OpenLibraryAuthorWork] = []
        for item in batch:
            pair = (item.author_key, item.work_key)
            if pair not in seen:
                seen.add(pair)
                unique.append(item)
        return unique

    def _deduplicate_isbns_batch(
        self, batch: list[OpenLibraryEditionIsbn]
    ) -> list[OpenLibraryEditionIsbn]:
        """Deduplicate ISBN batch by composite key.

        Parameters
        ----------
        batch : list[OpenLibraryEditionIsbn]
            Batch of ISBN relationships.

        Returns
        -------
        list[OpenLibraryEditionIsbn]
            Deduplicated batch.
        """
        seen: set[tuple[str, str]] = set()
        unique: list[OpenLibraryEditionIsbn] = []
        for item in batch:
            pair = (item.edition_key, item.isbn)
            if pair not in seen:
                seen.add(pair)
                unique.append(item)
        return unique

    def _commit_batches(
        self,
        session: Session,
        *batches: list[Any],
    ) -> None:
        """Commit multiple batches to database.

        Deduplicates author_works and edition_isbns batches before committing
        to handle cases where the same work/edition appears multiple times
        in the dump file.

        Parameters
        ----------
        session : Session
            Database session.
        *batches : list[Any]
            Variable number of batches to commit.
        """
        has_data = False
        for batch in batches:
            if not batch:
                continue

            # Deduplicate author_works and edition_isbns batches
            # Check first element to determine batch type
            first_item = batch[0]
            if isinstance(first_item, OpenLibraryAuthorWork):
                batch = self._deduplicate_author_works_batch(batch)
            elif isinstance(first_item, OpenLibraryEditionIsbn):
                batch = self._deduplicate_isbns_batch(batch)

            if batch:
                session.bulk_save_objects(batch)
                has_data = True

        if has_data:
            session.commit()

    def _process_works_file(
        self,
        file_path: Path,
        session: Session,
        update_progress: Callable[[float, dict[str, Any] | None], None],
        progress_offset: float,
        progress_scale: float,
    ) -> tuple[int, int]:
        """Process works dump file and extract author_works relationships.

        Parameters
        ----------
        file_path : Path
            Path to works dump file.
        session : Session
            Database session.
        update_progress : Callable
            Progress update callback.
        progress_offset : float
            Starting progress value (0.0-1.0).
        progress_scale : float
            Scale factor for this file's progress.

        Returns
        -------
        tuple[int, int]
            Tuple of (works_count, author_works_count).
        """
        logger.info("Processing works file: %s", file_path.name)

        if not file_path.exists():
            logger.warning("File not found: %s", file_path)
            return (0, 0)

        works_count = 0
        author_works_count = 0
        works_batch = []
        author_works_batch = []

        def _raise_cancelled() -> None:
            """Raise InterruptedError for cancelled task."""
            msg = "Task cancelled"
            raise InterruptedError(msg)

        try:
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                for line in f:
                    if self.check_cancelled():
                        _raise_cancelled()

                    parsed = self._parse_line(line)
                    if parsed is None:
                        continue

                    record_type, key, revision, last_modified, data = parsed

                    # Only process work records
                    if not key.startswith("/works/"):
                        continue

                    work = OpenLibraryWork(
                        type=record_type,
                        key=key,
                        revision=revision,
                        last_modified=last_modified,
                        data=data,
                    )
                    works_batch.append(work)
                    works_count += 1

                    # Extract author_works relationships from data
                    extracted_author_works = self._extract_author_works(data, key)
                    author_works_batch.extend(extracted_author_works)
                    author_works_count += len(extracted_author_works)

                    if len(works_batch) >= self.batch_size:
                        self._commit_batches(session, works_batch, author_works_batch)
                        works_batch = []
                        author_works_batch = []
                        self._update_progress_if_needed(
                            works_count,
                            progress_offset,
                            progress_scale,
                            file_path.name,
                            "works",
                            update_progress,
                        )

                # Insert remaining
                self._commit_batches(session, works_batch, author_works_batch)

        except Exception:
            logger.exception("Error processing works file %s", file_path)
            session.rollback()
            raise

        return (works_count, author_works_count)

    def _extract_work_key(self, data: dict[str, Any]) -> str | None:
        """Extract work key from edition data.

        Parameters
        ----------
        data : dict[str, Any]
            Edition data dictionary.

        Returns
        -------
        str | None
            Work key if found, None otherwise.
        """
        works = data.get("works", [])
        if isinstance(works, list) and len(works) > 0:
            work_ref = works[0]
            if isinstance(work_ref, dict):
                return work_ref.get("key")
        return None

    def _extract_isbns(
        self, data: dict[str, Any], edition_key: str
    ) -> list[OpenLibraryEditionIsbn]:
        """Extract ISBNs from edition data.

        Deduplicates ISBNs to prevent unique constraint violations.
        The same ISBN may appear in multiple fields (isbn_13, isbn_10, isbn).

        Parameters
        ----------
        data : dict[str, Any]
            Edition data dictionary.
        edition_key : str
            Edition key identifier.

        Returns
        -------
        list[OpenLibraryEditionIsbn]
            List of unique ISBN objects.
        """
        isbns = []
        seen_isbns: set[str] = set()
        isbn_fields = ["isbn_13", "isbn_10", "isbn"]
        for isbn_field in isbn_fields:
            isbn_list = data.get(isbn_field, [])
            if isinstance(isbn_list, list):
                for isbn in isbn_list:
                    if isinstance(isbn, str):
                        isbn_clean = isbn.strip()
                        if isbn_clean and isbn_clean not in seen_isbns:
                            seen_isbns.add(isbn_clean)
                            isbns.append(
                                OpenLibraryEditionIsbn(
                                    edition_key=edition_key, isbn=isbn_clean
                                )
                            )
        return isbns

    def _process_editions_file(
        self,
        file_path: Path,
        session: Session,
        update_progress: Callable[[float, dict[str, Any] | None], None],
        progress_offset: float,
        progress_scale: float,
    ) -> tuple[int, int]:
        """Process editions dump file and extract edition_isbns.

        Parameters
        ----------
        file_path : Path
            Path to editions dump file.
        session : Session
            Database session.
        update_progress : Callable
            Progress update callback.
        progress_offset : float
            Starting progress value (0.0-1.0).
        progress_scale : float
            Scale factor for this file's progress.

        Returns
        -------
        tuple[int, int]
            Tuple of (editions_count, isbns_count).
        """
        logger.info("Processing editions file: %s", file_path.name)

        if not file_path.exists():
            logger.warning("File not found: %s", file_path)
            return (0, 0)

        editions_count = 0
        isbns_count = 0
        editions_batch = []
        isbns_batch = []

        def _raise_cancelled() -> None:
            """Raise InterruptedError for cancelled task."""
            msg = "Task cancelled"
            raise InterruptedError(msg)

        try:
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                for line in f:
                    if self.check_cancelled():
                        _raise_cancelled()

                    parsed = self._parse_line(line)
                    if parsed is None:
                        continue

                    record_type, key, revision, last_modified, data = parsed

                    # Only process edition records
                    if not key.startswith("/editions/"):
                        continue

                    # Extract work_key from data
                    work_key = self._extract_work_key(data)

                    edition = OpenLibraryEdition(
                        type=record_type,
                        key=key,
                        revision=revision,
                        last_modified=last_modified,
                        data=data,
                        work_key=work_key,
                    )
                    editions_batch.append(edition)
                    editions_count += 1

                    # Extract ISBNs from data
                    extracted_isbns = self._extract_isbns(data, key)
                    isbns_batch.extend(extracted_isbns)
                    isbns_count += len(extracted_isbns)

                    if len(editions_batch) >= self.batch_size:
                        self._commit_batches(session, editions_batch, isbns_batch)
                        editions_batch = []
                        isbns_batch = []
                        self._update_progress_if_needed(
                            editions_count,
                            progress_offset,
                            progress_scale,
                            file_path.name,
                            "editions",
                            update_progress,
                        )

                # Insert remaining
                self._commit_batches(session, editions_batch, isbns_batch)

        except Exception:
            logger.exception("Error processing editions file %s", file_path)
            session.rollback()
            raise

        return (editions_count, isbns_count)

    def _update_progress_if_needed(
        self,
        processed_count: int,
        progress_offset: float,
        progress_scale: float,
        file_name: str,
        table_name: str,
        update_progress: Callable[[float, dict[str, Any] | None], None],
    ) -> None:
        """Update progress if threshold reached.

        Parameters
        ----------
        processed_count : int
            Number of records processed so far.
        progress_offset : float
            Starting progress value (0.0-1.0).
        progress_scale : float
            Scale factor for this file's progress.
        file_name : str
            Name of file being processed.
        table_name : str
            Target table name.
        update_progress : Callable
            Progress update callback.
        """
        if processed_count % 100000 == 0:
            # Rough progress estimation
            current_progress = progress_offset + (0.1 * progress_scale)
            update_progress(
                min(current_progress, 0.99),
                {
                    "current_file": file_name,
                    "processed_records": processed_count,
                    "status": f"Processing {table_name}...",
                },
            )

    def _get_tables_to_truncate(self) -> list[str]:
        """Get list of tables to truncate based on enabled file types.

        Returns
        -------
        list[str]
            List of table names to truncate.
        """
        tables_to_truncate = []
        if self.process_authors:
            tables_to_truncate.append("openlibrary_authors")
        if self.process_works:
            tables_to_truncate.append("openlibrary_works")
            tables_to_truncate.append("openlibrary_author_works")
        if self.process_editions:
            tables_to_truncate.append("openlibrary_editions")
            tables_to_truncate.append("openlibrary_edition_isbns")
        return tables_to_truncate

    def _truncate_tables(
        self,
        session: Session,
        update_progress: Callable[[float, dict[str, Any] | None], None],
    ) -> None:
        """Truncate tables for enabled file types.

        Parameters
        ----------
        session : Session
            Database session.
        update_progress : Callable
            Progress update callback.
        """
        update_progress(0.0, {"status": "Clearing existing data..."})
        tables_to_truncate = self._get_tables_to_truncate()
        if tables_to_truncate:
            session.connection().execute(
                text(f"TRUNCATE TABLE {', '.join(tables_to_truncate)} CASCADE")
            )
            session.commit()

    def _validate_enabled_file_types(self) -> None:
        """Validate that at least one file type is enabled.

        Raises
        ------
        ValueError
            If no file types are enabled.
        """
        enabled_count = sum([
            self.process_authors,
            self.process_works,
            self.process_editions,
        ])
        if enabled_count == 0:
            msg = "At least one file type must be enabled for processing"
            raise ValueError(msg)

    def _process_all_files(
        self,
        session: Session,
        update_progress: Callable[[float, dict[str, Any] | None], None],
        progress_per_file: float,
    ) -> tuple[int, int, int, int, int]:
        """Process all enabled file types.

        Parameters
        ----------
        session : Session
            Database session.
        update_progress : Callable
            Progress update callback.
        progress_per_file : float
            Progress increment per file.

        Returns
        -------
        tuple[int, int, int, int, int]
            Tuple of (authors_count, works_count, author_works_count, editions_count, isbns_count).
        """
        current_progress = 0.01
        authors_count = 0
        works_count = 0
        author_works_count = 0
        editions_count = 0
        isbns_count = 0

        # Process Authors
        if self.process_authors:
            authors_file = self.dump_dir / "ol_dump_authors_latest.txt.gz"
            update_progress(
                current_progress,
                {
                    "status": "Processing authors...",
                    "current_file": authors_file.name,
                    "processed_records": 0,
                },
            )
            authors_count = self._process_authors_file(
                authors_file,
                session,
                update_progress,
                current_progress,
                progress_per_file,
            )
            current_progress += progress_per_file

        # Process Works
        if self.process_works:
            works_file = self.dump_dir / "ol_dump_works_latest.txt.gz"
            update_progress(
                current_progress,
                {
                    "status": "Processing works...",
                    "current_file": works_file.name,
                    "processed_records": 0,
                },
            )
            works_count, author_works_count = self._process_works_file(
                works_file,
                session,
                update_progress,
                current_progress,
                progress_per_file,
            )
            current_progress += progress_per_file

        # Process Editions (if enabled and file exists)
        if self.process_editions:
            editions_file = self.dump_dir / "ol_dump_editions_latest.txt.gz"
            if editions_file.exists():
                update_progress(
                    current_progress,
                    {
                        "status": "Processing editions...",
                        "current_file": editions_file.name,
                        "processed_records": 0,
                    },
                )
                editions_count, isbns_count = self._process_editions_file(
                    editions_file,
                    session,
                    update_progress,
                    current_progress,
                    progress_per_file,
                )
            else:
                logger.warning("Editions file not found: %s", editions_file)

        return (
            authors_count,
            works_count,
            author_works_count,
            editions_count,
            isbns_count,
        )

    def run(self, worker_context: dict[str, Any]) -> None:
        """Execute OpenLibrary dump ingestion task.

        Parameters
        ----------
        worker_context : dict[str, Any]
            Worker context containing session, task_service, update_progress.
        """
        session: Session = worker_context["session"]
        update_progress = worker_context["update_progress"]

        # Ensure base directory exists
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.dump_dir.mkdir(parents=True, exist_ok=True)

        try:
            if self.check_cancelled():
                return

            self._truncate_tables(session, update_progress)

            update_progress(
                0.01,
                {
                    "status": "Starting ingestion...",
                    "current_file": "",
                    "processed_records": 0,
                },
            )

            self._validate_enabled_file_types()

            enabled_count = sum([
                self.process_authors,
                self.process_works,
                self.process_editions,
            ])
            progress_per_file = 0.98 / enabled_count

            (
                authors_count,
                works_count,
                author_works_count,
                editions_count,
                isbns_count,
            ) = self._process_all_files(session, update_progress, progress_per_file)

            update_progress(
                1.0,
                {
                    "status": "Completed",
                    "current_file": "",
                    "processed_records": (
                        authors_count
                        + works_count
                        + author_works_count
                        + editions_count
                        + isbns_count
                    ),
                },
            )

            logger.info(
                "Ingestion complete. Authors: %d, Works: %d, Author-Works: %d, "
                "Editions: %d, ISBNs: %d",
                authors_count,
                works_count,
                author_works_count,
                editions_count,
                isbns_count,
            )

        except Exception:
            logger.exception("Task %s failed", self.task_id)
            session.rollback()
            raise
