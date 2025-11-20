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

Ingests OpenLibrary dump files into a local optimized SQLite database
for fast lookups during library scanning.
"""

import gzip
import json
import logging
import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fundamental.services.tasks.base import BaseTask

logger = logging.getLogger(__name__)


class OpenLibraryDumpIngestTask(BaseTask):
    """Task for ingesting OpenLibrary dump files into local SQLite DB.

    Reads compressed dump files and populates a local SQLite database
    optimized for read performance.
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
            Task metadata. Can contain 'data_directory'.
        """
        super().__init__(task_id, user_id, metadata)
        data_directory = metadata.get("data_directory", "/data")
        self.base_dir = Path(data_directory) / "openlibrary"
        self.dump_dir = self.base_dir / "dump"
        self.db_path = self.base_dir / "openlibrary.db"
        self.batch_size = 10000

    def _init_db(self, conn: sqlite3.Connection) -> None:
        """Initialize database schema.

        Parameters
        ----------
        conn : sqlite3.Connection
            Database connection.
        """
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = -2000000")  # ~2GB cache

        # Authors table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS authors (
                key TEXT PRIMARY KEY,
                name TEXT,
                data JSON
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_authors_name ON authors(name)")

        # Works table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS works (
                key TEXT PRIMARY KEY,
                title TEXT,
                data JSON
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_works_title ON works(title)")

    def _process_file(
        self,
        file_path: Path,
        table_name: str,
        conn: sqlite3.Connection,
        update_progress: Callable[[float, dict[str, Any] | None], None],
        progress_offset: float,
        progress_scale: float,
    ) -> int:
        """Process a single dump file.

        Parameters
        ----------
        file_path : Path
            Path to .txt.gz dump file.
        table_name : str
            Target table name ('authors' or 'works').
        conn : sqlite3.Connection
            Database connection.
        update_progress : Any
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
        logger.info("Processing %s into table %s", file_path.name, table_name)

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

                    record = self._parse_line(line, table_name)
                    if record is None:
                        continue

                    batch.append(record)
                    processed_count += 1

                    if len(batch) >= self.batch_size:
                        self._insert_batch(conn, table_name, batch)
                        batch = []
                        self._update_progress_if_needed(
                            processed_count,
                            progress_offset,
                            progress_scale,
                            file_path.name,
                            table_name,
                            update_progress,
                        )

                # Insert remaining
                if batch:
                    self._insert_batch(conn, table_name, batch)

        except Exception:
            logger.exception("Error processing file %s", file_path)
            raise

        return processed_count

    def _parse_line(
        self, line: str, table_name: str
    ) -> tuple[str, str | None, str] | None:
        """Parse a single line from dump file.

        Parameters
        ----------
        line : str
            Line from dump file.
        table_name : str
            Target table name ('authors' or 'works').

        Returns
        -------
        tuple[str, str | None, str] | None
            Tuple of (key, name_or_title, json_str) or None if invalid.
        """
        parts = line.split("\t")
        if len(parts) < 5:
            return None

        # Format: type, key, revision, last_modified, json
        # We only need key and json
        key = parts[1]
        json_str = parts[4]

        # Extract name/title for indexing
        name_or_title = None
        try:
            data = json.loads(json_str)
            if table_name == "authors":
                name_or_title = data.get("name")
            elif table_name == "works":
                name_or_title = data.get("title")

            # Normalize key (remove /type/ prefix)
            key = key.split("/")[-1]
        except json.JSONDecodeError:
            return None
        else:
            return (key, name_or_title, json_str)

    def _insert_batch(
        self,
        conn: sqlite3.Connection,
        table_name: str,
        batch: list[tuple[str, str | None, str]],
    ) -> None:
        """Insert a batch of records into the database.

        Parameters
        ----------
        conn : sqlite3.Connection
            Database connection.
        table_name : str
            Target table name ('authors' or 'works').
        batch : list[tuple[str, str | None, str]]
            Batch of records to insert.
        """
        # Whitelist table names and queries to prevent SQL injection
        query_map = {
            "authors": (
                "INSERT OR REPLACE INTO authors (key, name, data) VALUES (?, ?, ?)"
            ),
            "works": (
                "INSERT OR REPLACE INTO works (key, title, data) VALUES (?, ?, ?)"
            ),
        }
        if table_name not in query_map:
            msg = f"Invalid table name: {table_name}"
            raise ValueError(msg)

        query = query_map[table_name]
        conn.executemany(query, batch)
        conn.commit()

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

    def run(self, worker_context: dict[str, Any]) -> None:
        """Execute OpenLibrary dump ingestion task.

        Parameters
        ----------
        worker_context : dict[str, Any]
            Worker context.
        """
        update_progress = worker_context["update_progress"]

        # Ensure base directory exists
        self.base_dir.mkdir(parents=True, exist_ok=True)

        try:
            if self.check_cancelled():
                return

            # Delete existing database file for fresh ingestion
            update_progress(0.0, {"status": "Removing existing database..."})
            if self.db_path.exists():
                self.db_path.unlink()
            # Also remove WAL and SHM files if they exist
            wal_path = self.db_path.with_suffix(self.db_path.suffix + "-wal")
            shm_path = self.db_path.with_suffix(self.db_path.suffix + "-shm")
            if wal_path.exists():
                wal_path.unlink()
            if shm_path.exists():
                shm_path.unlink()

            update_progress(0.01, {"status": "Initializing database..."})

            with sqlite3.connect(self.db_path) as conn:
                self._init_db(conn)

                # Process Authors
                authors_file = self.dump_dir / "ol_dump_authors_latest.txt.gz"
                update_progress(0.05, {"status": "Processing authors..."})
                authors_count = self._process_file(
                    authors_file, "authors", conn, update_progress, 0.05, 0.45
                )

                # Process Works
                works_file = self.dump_dir / "ol_dump_works_latest.txt.gz"
                update_progress(0.5, {"status": "Processing works..."})
                works_count = self._process_file(
                    works_file, "works", conn, update_progress, 0.5, 0.45
                )

                # Optimize DB
                update_progress(0.95, {"status": "Optimizing database..."})
                conn.execute("ANALYZE")

            update_progress(
                1.0,
                {
                    "status": "Completed",
                    "authors_processed": authors_count,
                    "works_processed": works_count,
                },
            )

            logger.info(
                "Ingestion complete. Authors: %d, Works: %d", authors_count, works_count
            )

        except Exception:
            logger.exception("Task %s failed", self.task_id)
            raise
