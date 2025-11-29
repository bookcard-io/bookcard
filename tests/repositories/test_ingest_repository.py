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

"""Tests for ingest repository to achieve 100% coverage."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from fundamental.models.ingest import (
    IngestAudit,
    IngestConfig,
    IngestHistory,
    IngestRetry,
    IngestStatus,
)
from fundamental.repositories.ingest_repository import (
    IngestAuditRepository,
    IngestConfigRepository,
    IngestHistoryRepository,
    IngestRetryRepository,
)
from tests.conftest import DummySession


@pytest.fixture
def session() -> DummySession:
    """Create a dummy database session."""
    return DummySession()


@pytest.fixture
def history_repo(session: DummySession) -> IngestHistoryRepository:
    """Create IngestHistoryRepository instance."""
    return IngestHistoryRepository(session=session)  # type: ignore[arg-type]


@pytest.fixture
def retry_repo(session: DummySession) -> IngestRetryRepository:
    """Create IngestRetryRepository instance."""
    return IngestRetryRepository(session=session)  # type: ignore[arg-type]


@pytest.fixture
def audit_repo(session: DummySession) -> IngestAuditRepository:
    """Create IngestAuditRepository instance."""
    return IngestAuditRepository(session=session)  # type: ignore[arg-type]


@pytest.fixture
def config_repo(session: DummySession) -> IngestConfigRepository:
    """Create IngestConfigRepository instance."""
    return IngestConfigRepository(session=session)  # type: ignore[arg-type]


class TestIngestHistoryRepository:
    """Test IngestHistoryRepository."""

    def test_init(
        self,
        session: DummySession,
    ) -> None:
        """Test IngestHistoryRepository initialization."""
        repo = IngestHistoryRepository(session=session)  # type: ignore[arg-type]
        assert repo._session == session
        assert repo._model_type == IngestHistory

    def test_get_by_status(
        self,
        history_repo: IngestHistoryRepository,
        session: DummySession,
    ) -> None:
        """Test get_by_status filters by status."""
        history1 = IngestHistory(
            id=1,
            file_path="/path/to/file1.epub",
            status=IngestStatus.PENDING,
        )
        history3 = IngestHistory(
            id=3,
            file_path="/path/to/file3.epub",
            status=IngestStatus.PENDING,
        )

        # DummySession doesn't filter WHERE clauses, so set only matching results
        session.set_exec_result([history1, history3])

        result = history_repo.get_by_status(IngestStatus.PENDING)

        assert len(result) == 2
        assert history1 in result
        assert history3 in result

    def test_get_pending_retries(
        self,
        history_repo: IngestHistoryRepository,
        session: DummySession,
    ) -> None:
        """Test get_pending_retries returns due retries."""
        now = datetime.now(UTC)
        retry = IngestRetry(
            id=1,
            history_id=1,
            retry_count=1,
            next_retry_at=now - timedelta(seconds=1),
            error_message="Error",
        )

        session.set_exec_result([retry])

        result = history_repo.get_pending_retries()

        assert len(result) == 1
        assert result[0] == retry

    def test_get_pending_retries_not_due(
        self,
        history_repo: IngestHistoryRepository,
        session: DummySession,
    ) -> None:
        """Test get_pending_retries excludes retries not yet due."""
        session.set_exec_result([])

        result = history_repo.get_pending_retries()

        assert len(result) == 0

    def test_get_by_file_path(
        self,
        history_repo: IngestHistoryRepository,
        session: DummySession,
    ) -> None:
        """Test get_by_file_path finds history by file path."""
        history = IngestHistory(
            id=1,
            file_path="/path/to/file.epub",
            status=IngestStatus.PENDING,
        )

        session.set_exec_result([history])

        result = history_repo.get_by_file_path("/path/to/file.epub")

        assert result == history

    def test_get_by_file_path_not_found(
        self,
        history_repo: IngestHistoryRepository,
        session: DummySession,
    ) -> None:
        """Test get_by_file_path returns None when not found."""
        session.set_exec_result([])

        result = history_repo.get_by_file_path("/nonexistent/file.epub")

        assert result is None


class TestIngestRetryRepository:
    """Test IngestRetryRepository."""

    def test_init(
        self,
        session: DummySession,
    ) -> None:
        """Test IngestRetryRepository initialization."""
        repo = IngestRetryRepository(session=session)  # type: ignore[arg-type]
        assert repo._session == session
        assert repo._model_type == IngestRetry

    def test_get_due_retries(
        self,
        retry_repo: IngestRetryRepository,
        session: DummySession,
    ) -> None:
        """Test get_due_retries returns retries that are due."""
        now = datetime.now(UTC)
        retry1 = IngestRetry(
            id=1,
            history_id=1,
            retry_count=1,
            next_retry_at=now - timedelta(seconds=1),
            error_message="Error 1",
        )
        retry2 = IngestRetry(
            id=2,
            history_id=2,
            retry_count=1,
            next_retry_at=now - timedelta(seconds=10),
            error_message="Error 2",
        )

        session.set_exec_result([retry1, retry2])

        result = retry_repo.get_due_retries()

        assert len(result) == 2
        assert retry1 in result
        assert retry2 in result

    def test_get_due_retries_not_due(
        self,
        retry_repo: IngestRetryRepository,
        session: DummySession,
    ) -> None:
        """Test get_due_retries excludes retries not yet due."""
        session.set_exec_result([])

        result = retry_repo.get_due_retries()

        assert len(result) == 0

    def test_create_retry(
        self,
        retry_repo: IngestRetryRepository,
        session: DummySession,
    ) -> None:
        """Test create_retry creates a new retry record."""
        now = datetime.now(UTC)
        next_retry = now + timedelta(seconds=300)

        result = retry_repo.create_retry(
            history_id=1,
            error="Test error",
            retry_count=1,
            next_retry_at=next_retry,
        )

        assert result.history_id == 1
        assert result.retry_count == 1
        assert result.next_retry_at == next_retry
        assert result.error_message == "Test error"
        assert result in session.added

    def test_get_by_history_id(
        self,
        retry_repo: IngestRetryRepository,
        session: DummySession,
    ) -> None:
        """Test get_by_history_id finds retry by history ID."""
        retry = IngestRetry(
            id=1,
            history_id=1,
            retry_count=1,
            next_retry_at=datetime.now(UTC),
            error_message="Error",
        )

        session.set_exec_result([retry])

        result = retry_repo.get_by_history_id(1)

        assert result == retry

    def test_get_by_history_id_not_found(
        self,
        retry_repo: IngestRetryRepository,
        session: DummySession,
    ) -> None:
        """Test get_by_history_id returns None when not found."""
        session.set_exec_result([])

        result = retry_repo.get_by_history_id(999)

        assert result is None


class TestIngestAuditRepository:
    """Test IngestAuditRepository."""

    def test_init(
        self,
        session: DummySession,
    ) -> None:
        """Test IngestAuditRepository initialization."""
        repo = IngestAuditRepository(session=session)  # type: ignore[arg-type]
        assert repo._session == session
        assert repo._model_type == IngestAudit

    def test_log_action(
        self,
        audit_repo: IngestAuditRepository,
        session: DummySession,
    ) -> None:
        """Test log_action creates audit record."""
        result = audit_repo.log_action(
            action="file_discovered",
            file_path="/path/to/file.epub",
            metadata={"key": "value"},
            history_id=1,
            user_id=2,
        )

        assert result.action == "file_discovered"
        assert result.file_path == "/path/to/file.epub"
        assert result.audit_metadata == {"key": "value"}
        assert result.history_id == 1
        assert result.user_id == 2
        assert result in session.added

    def test_log_action_minimal(
        self,
        audit_repo: IngestAuditRepository,
        session: DummySession,
    ) -> None:
        """Test log_action with minimal parameters."""
        result = audit_repo.log_action(
            action="file_discovered",
            file_path="/path/to/file.epub",
        )

        assert result.action == "file_discovered"
        assert result.file_path == "/path/to/file.epub"
        assert result.audit_metadata is None
        assert result.history_id is None
        assert result.user_id is None

    def test_get_by_history_id(
        self,
        audit_repo: IngestAuditRepository,
        session: DummySession,
    ) -> None:
        """Test get_by_history_id returns audit records for history."""
        audit1 = IngestAudit(
            id=1,
            action="file_discovered",
            file_path="/path/to/file.epub",
            history_id=1,
        )
        audit2 = IngestAudit(
            id=2,
            action="metadata_fetched",
            file_path="/path/to/file.epub",
            history_id=1,
        )

        # DummySession doesn't filter WHERE clauses, so set only matching results
        session.set_exec_result([audit1, audit2])

        result = audit_repo.get_by_history_id(1)

        assert len(result) == 2
        assert audit1 in result
        assert audit2 in result

    def test_get_by_history_id_empty(
        self,
        audit_repo: IngestAuditRepository,
        session: DummySession,
    ) -> None:
        """Test get_by_history_id returns empty list when no records."""
        session.set_exec_result([])

        result = audit_repo.get_by_history_id(999)

        assert result == []


class TestIngestConfigRepository:
    """Test IngestConfigRepository."""

    def test_init(
        self,
        session: DummySession,
    ) -> None:
        """Test IngestConfigRepository initialization."""
        repo = IngestConfigRepository(session=session)  # type: ignore[arg-type]
        assert repo._session == session
        assert repo._model_type == IngestConfig

    def test_get_config_existing(
        self,
        config_repo: IngestConfigRepository,
        session: DummySession,
    ) -> None:
        """Test get_config returns existing config."""
        config = IngestConfig(
            id=1,
            ingest_dir="/data/books_ingest",
            enabled=True,
        )

        session.set_exec_result([config])

        result = config_repo.get_config()

        assert result == config

    def test_get_config_creates_default(
        self,
        config_repo: IngestConfigRepository,
        session: DummySession,
    ) -> None:
        """Test get_config creates default config when none exists."""
        session.set_exec_result([None])

        with patch.dict(os.environ, {"BOOKS_INGEST_DIR": "/custom/ingest"}):
            result = config_repo.get_config()

        assert result.ingest_dir == "/custom/ingest"
        assert result.enabled is True
        assert result.metadata_providers == ["google", "hardcover", "openlibrary"]
        assert result.metadata_merge_strategy == "merge_best"
        assert result in session.added
        assert session.commit_count > 0

    def test_get_config_default_env_var(
        self,
        config_repo: IngestConfigRepository,
        session: DummySession,
    ) -> None:
        """Test get_config uses default ingest_dir when env var not set."""
        session.set_exec_result([None])

        with patch.dict(os.environ, {}, clear=True):
            # Remove BOOKS_INGEST_DIR if it exists
            os.environ.pop("BOOKS_INGEST_DIR", None)
            result = config_repo.get_config()

        assert result.ingest_dir == "/data/books_ingest"

    def test_update_config(
        self,
        config_repo: IngestConfigRepository,
        session: DummySession,
    ) -> None:
        """Test update_config updates existing config."""
        config = IngestConfig(
            id=1,
            ingest_dir="/data/books_ingest",
            enabled=True,
        )

        session.set_exec_result([config])

        result = config_repo.update_config(enabled=False, ingest_dir="/new/path")

        assert result.enabled is False
        assert result.ingest_dir == "/new/path"
        assert session.commit_count > 0

    def test_update_config_creates_if_needed(
        self,
        config_repo: IngestConfigRepository,
        session: DummySession,
    ) -> None:
        """Test update_config creates config if it doesn't exist."""
        # First call returns None (no config), second call returns created config
        created_config = IngestConfig(
            id=1,
            ingest_dir="/data/books_ingest",
            enabled=True,
        )

        session.set_exec_result([None, created_config])

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("BOOKS_INGEST_DIR", None)
            result = config_repo.update_config(enabled=False)

        assert result.enabled is False
        assert session.commit_count > 0

    def test_update_config_ignores_invalid_attributes(
        self,
        config_repo: IngestConfigRepository,
        session: DummySession,
    ) -> None:
        """Test update_config ignores attributes that don't exist on config."""
        config = IngestConfig(
            id=1,
            ingest_dir="/data/books_ingest",
            enabled=True,
        )

        session.set_exec_result([config])

        result = config_repo.update_config(
            enabled=False, invalid_attribute="should be ignored"
        )

        assert result.enabled is False
        assert not hasattr(result, "invalid_attribute")
