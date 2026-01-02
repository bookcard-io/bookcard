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

"""Tests for ProwlarrSyncTask."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from bookcard.services.tasks.prowlarr_sync_task import ProwlarrSyncTask


@pytest.fixture
def mock_session() -> MagicMock:
    """Return mock Session."""
    return MagicMock(spec=Session)


@pytest.fixture
def worker_context(mock_session: MagicMock) -> dict[str, MagicMock]:
    """Return mock worker context."""
    return {
        "session": mock_session,
        "task_service": MagicMock(),
        "update_progress": MagicMock(),
    }


class TestProwlarrSyncTask:
    """Tests for ProwlarrSyncTask."""

    def test_run_success(
        self,
        worker_context: dict[str, MagicMock],
        mock_session: MagicMock,
    ) -> None:
        """Test run executes sync successfully."""
        task = ProwlarrSyncTask(task_id=1, user_id=1)

        mock_config = MagicMock()
        mock_config.encryption_key = "dummy-key"

        with (
            patch(
                "bookcard.services.tasks.prowlarr_sync_task.ProwlarrSyncService"
            ) as mock_service_cls,
            patch("bookcard.services.tasks.prowlarr_sync_task.DataEncryptor"),
            patch(
                "bookcard.services.tasks.prowlarr_sync_task.AppConfig.from_env",
                return_value=mock_config,
            ),
        ):
            mock_service = mock_service_cls.return_value
            mock_service.sync_indexers.return_value = {"added": 1, "updated": 0}

            task.run(worker_context)

            # Verify service initialization
            mock_service_cls.assert_called_once()
            args, kwargs = mock_service_cls.call_args
            assert args[0] == mock_session
            assert kwargs["encryptor"] is not None

            # Verify sync called
            mock_service.sync_indexers.assert_called_once()

            # Verify metadata updated
            assert task.metadata["stats"] == {"added": 1, "updated": 0}

    def test_run_failure(
        self,
        worker_context: dict[str, MagicMock],
    ) -> None:
        """Test run handles exceptions."""
        task = ProwlarrSyncTask(task_id=1, user_id=1)

        mock_config = MagicMock()
        mock_config.encryption_key = "dummy-key"

        with (
            patch(
                "bookcard.services.tasks.prowlarr_sync_task.ProwlarrSyncService"
            ) as mock_service_cls,
            patch("bookcard.services.tasks.prowlarr_sync_task.DataEncryptor"),
            patch(
                "bookcard.services.tasks.prowlarr_sync_task.AppConfig.from_env",
                return_value=mock_config,
            ),
        ):
            mock_service = mock_service_cls.return_value
            mock_service.sync_indexers.side_effect = Exception("Sync failed")

            with pytest.raises(Exception, match="Sync failed"):
                task.run(worker_context)

    def test_run_no_encryptor_if_no_key(
        self,
        worker_context: dict[str, MagicMock],
        mock_session: MagicMock,
    ) -> None:
        """Test run initializes service without encryptor if key is missing."""
        task = ProwlarrSyncTask(task_id=1, user_id=1)

        with (
            patch(
                "bookcard.services.tasks.prowlarr_sync_task.ProwlarrSyncService"
            ) as mock_service_cls,
            patch(
                "bookcard.services.tasks.prowlarr_sync_task.DataEncryptor"
            ) as mock_encryptor_cls,
            patch(
                "bookcard.services.tasks.prowlarr_sync_task.AppConfig.from_env",
                side_effect=ValueError("Key missing"),
            ),
        ):
            mock_service = mock_service_cls.return_value
            mock_service.sync_indexers.return_value = {}

            task.run(worker_context)

            # Verify service initialization with no encryptor
            mock_service_cls.assert_called_once()
            _, kwargs = mock_service_cls.call_args
            assert kwargs["encryptor"] is None

            # Encryptor not initialized
            mock_encryptor_cls.assert_not_called()
