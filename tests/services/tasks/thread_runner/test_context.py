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

"""Tests for TaskContextBuilder."""

from __future__ import annotations

from unittest.mock import MagicMock

from bookcard.models.tasks import TaskType
from bookcard.services.tasks.thread_runner.context import TaskContextBuilder


class TestTaskContextBuilder:
    """Tests for TaskContextBuilder."""

    def test_build_service_context(self) -> None:
        """Test building service context."""
        mock_session = MagicMock()
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session

        mock_service = MagicMock()
        mock_service_factory = MagicMock(return_value=mock_service)

        mock_task_factory = MagicMock()

        builder = TaskContextBuilder(
            session_factory=mock_session_factory,
            service_factory=mock_service_factory,
            task_factory=mock_task_factory,
        )

        with builder.build_service_context() as (session, service):
            assert session == mock_session
            assert service == mock_service

        mock_session_factory.assert_called_once()
        mock_service_factory.assert_called_once_with(mock_session)

    def test_create_task_instance(self) -> None:
        """Test creating task instance."""
        mock_task_factory = MagicMock()
        builder = TaskContextBuilder(
            session_factory=MagicMock(),
            service_factory=MagicMock(),
            task_factory=mock_task_factory,
        )

        task_id = 1
        user_id = 2
        payload = {"key": "value"}
        metadata = {"meta": "data"}
        task_type = TaskType.BOOK_UPLOAD

        builder.create_task_instance(task_id, user_id, payload, metadata, task_type)

        expected_metadata = metadata.copy()
        expected_metadata["task_type"] = task_type
        expected_metadata.update(payload)

        mock_task_factory.assert_called_once_with(task_id, user_id, expected_metadata)

    def test_create_task_instance_no_metadata(self) -> None:
        """Test creating task instance with no metadata."""
        mock_task_factory = MagicMock()
        builder = TaskContextBuilder(
            session_factory=MagicMock(),
            service_factory=MagicMock(),
            task_factory=mock_task_factory,
        )

        task_id = 1
        user_id = 2
        payload = {"key": "value"}
        task_type = TaskType.BOOK_UPLOAD

        builder.create_task_instance(task_id, user_id, payload, None, task_type)

        expected_metadata = {"task_type": task_type}
        expected_metadata.update(payload)

        mock_task_factory.assert_called_once_with(task_id, user_id, expected_metadata)
