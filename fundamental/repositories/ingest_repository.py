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

"""Ingest repositories.

Repositories for ingest management models. Follows SRP and IOC principles.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Session, select

from fundamental.models.ingest import (
    IngestAudit,
    IngestConfig,
    IngestHistory,
    IngestRetry,
    IngestStatus,
)
from fundamental.repositories.base import Repository


class IngestHistoryRepository(Repository[IngestHistory]):
    """Repository for ingest history operations.

    Provides CRUD operations and query methods for ingest history records.
    """

    def __init__(self, session: Session) -> None:  # type: ignore[type-arg]
        """Initialize ingest history repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        super().__init__(session, IngestHistory)

    def get_by_status(self, status: IngestStatus) -> list[IngestHistory]:
        """Get all ingest records with the specified status.

        Parameters
        ----------
        status : IngestStatus
            Status to filter by.

        Returns
        -------
        list[IngestHistory]
            List of ingest history records with the specified status.
        """
        stmt = select(IngestHistory).where(IngestHistory.status == status)
        return list(self._session.exec(stmt).all())

    def get_pending_retries(self) -> list[IngestRetry]:
        """Get all pending retry records.

        Returns
        -------
        list[IngestRetry]
            List of retry records that are due for retry.
        """
        now = datetime.now(UTC)
        stmt = (
            select(IngestRetry)
            .join(IngestHistory)
            .where(IngestRetry.next_retry_at <= now)
            .where(IngestHistory.status == IngestStatus.FAILED)
        )
        return list(self._session.exec(stmt).all())

    def get_by_file_path(self, file_path: str) -> IngestHistory | None:
        """Get ingest history by file path.

        Parameters
        ----------
        file_path : str
            File path to search for.

        Returns
        -------
        IngestHistory | None
            Ingest history record if found, None otherwise.
        """
        stmt = select(IngestHistory).where(IngestHistory.file_path == file_path)
        return self._session.exec(stmt).first()


class IngestRetryRepository(Repository[IngestRetry]):
    """Repository for ingest retry operations.

    Manages retry queue and retry scheduling.
    """

    def __init__(self, session: Session) -> None:  # type: ignore[type-arg]
        """Initialize ingest retry repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        super().__init__(session, IngestRetry)

    def get_due_retries(self) -> list[IngestRetry]:
        """Get all retry records that are due for retry.

        Returns
        -------
        list[IngestRetry]
            List of retry records that are due.
        """
        now = datetime.now(UTC)
        stmt = select(IngestRetry).where(IngestRetry.next_retry_at <= now)
        return list(self._session.exec(stmt).all())

    def create_retry(
        self,
        history_id: int,
        error: str,
        retry_count: int,
        next_retry_at: datetime,
    ) -> IngestRetry:
        """Create a new retry record.

        Parameters
        ----------
        history_id : int
            ID of the ingest history record to retry.
        error : str
            Error message from the failed attempt.
        retry_count : int
            Number of retry attempts (1-based).
        next_retry_at : datetime
            When the next retry should be attempted.

        Returns
        -------
        IngestRetry
            Created retry record.
        """
        retry = IngestRetry(
            history_id=history_id,
            retry_count=retry_count,
            next_retry_at=next_retry_at,
            error_message=error,
        )
        self.add(retry)
        return retry

    def get_by_history_id(self, history_id: int) -> IngestRetry | None:
        """Get retry record by history ID.

        Parameters
        ----------
        history_id : int
            Ingest history ID.

        Returns
        -------
        IngestRetry | None
            Retry record if found, None otherwise.
        """
        stmt = select(IngestRetry).where(IngestRetry.history_id == history_id)
        return self._session.exec(stmt).first()


class IngestAuditRepository(Repository[IngestAudit]):
    """Repository for ingest audit logging.

    Provides audit trail operations for ingest operations.
    """

    def __init__(self, session: Session) -> None:  # type: ignore[type-arg]
        """Initialize ingest audit repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        super().__init__(session, IngestAudit)

    def log_action(
        self,
        action: str,
        file_path: str,
        metadata: dict | None = None,
        history_id: int | None = None,
        user_id: int | None = None,
    ) -> IngestAudit:
        """Log an audit action.

        Parameters
        ----------
        action : str
            Action performed (e.g., 'file_discovered', 'metadata_fetched').
        file_path : str
            Path to the file being processed.
        metadata : dict | None
            Optional metadata about the action.
        history_id : int | None
            Optional ingest history ID.
        user_id : int | None
            Optional user ID who triggered the action.

        Returns
        -------
        IngestAudit
            Created audit record.
        """
        audit = IngestAudit(
            action=action,
            file_path=file_path,
            audit_metadata=metadata,
            history_id=history_id,
            user_id=user_id,
        )
        self.add(audit)
        return audit

    def get_by_history_id(self, history_id: int) -> list[IngestAudit]:
        """Get all audit records for a specific ingest history.

        Parameters
        ----------
        history_id : int
            Ingest history ID.

        Returns
        -------
        list[IngestAudit]
            List of audit records for the history.
        """
        stmt = select(IngestAudit).where(IngestAudit.history_id == history_id)
        return list(self._session.exec(stmt).all())


class IngestConfigRepository(Repository[IngestConfig]):
    """Repository for ingest configuration.

    Manages singleton ingest configuration.
    """

    def __init__(self, session: Session) -> None:  # type: ignore[type-arg]
        """Initialize ingest config repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        super().__init__(session, IngestConfig)

    def get_config(self) -> IngestConfig:
        """Get ingest configuration (singleton pattern).

        Returns the existing config or creates a default one if none exists.

        Returns
        -------
        IngestConfig
            Ingest configuration.
        """
        stmt = select(IngestConfig).limit(1)
        config = self._session.exec(stmt).first()
        if config is None:
            # Create default config
            import os

            ingest_dir = os.getenv("BOOKS_INGEST_DIR", "/app/books_ingest")
            config = IngestConfig(
                ingest_dir=ingest_dir,
                enabled=False,
                metadata_providers=["google", "hardcover", "openlibrary"],
                metadata_merge_strategy="merge_best",
                metadata_priority_order=["google", "hardcover", "openlibrary"],
                supported_formats=[
                    "acsm",
                    "azw",
                    "azw3",
                    "azw4",
                    "mobi",
                    "cbz",
                    "cbr",
                    "cb7",
                    "cbc",
                    "chm",
                    "djvu",
                    "docx",
                    "epub",
                    "fb2",
                    "fbz",
                    "html",
                    "htmlz",
                    "lit",
                    "lrf",
                    "odt",
                    "pdf",
                    "prc",
                    "pdb",
                    "pml",
                    "rb",
                    "rtf",
                    "snb",
                    "tcr",
                    "txtz",
                ],
                ignore_patterns=["*.tmp", "*.bak", "*.swp"],
                retry_max_attempts=3,
                retry_backoff_seconds=300,
                process_timeout_seconds=3600,
                auto_delete_after_ingest=True,
            )
            self.add(config)
            self._session.commit()
            self._session.refresh(config)
        return config

    def update_config(self, **kwargs: object) -> IngestConfig:
        """Update ingest configuration.

        Parameters
        ----------
        **kwargs : object
            Configuration fields to update.

        Returns
        -------
        IngestConfig
            Updated configuration.
        """
        config = self.get_config()
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        self._session.add(config)
        self._session.commit()
        self._session.refresh(config)
        return config
