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

"""Task execution context building."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from sqlmodel import Session

    from bookcard.models.tasks import TaskType
    from bookcard.services.task_service import TaskService
    from bookcard.services.tasks.base import BaseTask


class TaskContextBuilder:
    """Builds the context required for task execution.

    Handles creation of database sessions, services, and task instances.
    """

    def __init__(
        self,
        session_factory: Callable[[], Iterator[Session]],
        service_factory: Callable[[Session], TaskService],
        task_factory: Callable[[int, int, dict[str, Any]], BaseTask],
    ) -> None:
        """Initialize task context builder.

        Parameters
        ----------
        session_factory : Callable[[], Iterator[Session]]
            Callable that returns a session context manager.
        service_factory : Callable[[Session], TaskService]
            Callable that creates a TaskService from a session.
        task_factory : Callable[[int, int, dict[str, Any]], BaseTask]
            Factory function to create task instances.
        """
        self._session_factory = session_factory
        self._service_factory = service_factory
        self._task_factory = task_factory

    @contextlib.contextmanager
    def build_service_context(self) -> Iterator[tuple[Session, TaskService]]:
        """Create a session and task service context.

        Yields
        ------
        tuple[Session, TaskService]
            The database session and task service.
        """
        # The session_factory is expected to be a context manager (like _get_session)
        # We wrap it in our own context manager
        with self._session_factory() as session:
            service = self._service_factory(session)
            yield session, service

    def create_task_instance(
        self,
        task_id: int,
        user_id: int,
        payload: dict[str, Any],
        metadata: dict[str, Any] | None,
        task_type: TaskType,
    ) -> BaseTask:
        """Create a task instance.

        Parameters
        ----------
        task_id : int
            Task ID.
        user_id : int
            User ID.
        payload : dict[str, Any]
            Task payload.
        metadata : dict[str, Any] | None
            Task metadata.
        task_type : TaskType
            Task type.

        Returns
        -------
        BaseTask
            The created task instance.
        """
        # Merge payload into metadata as per original logic
        # This ensures tasks can access payload data in __init__
        task_metadata = (metadata or {}).copy()
        task_metadata["task_type"] = task_type
        task_metadata.update(payload)

        return self._task_factory(task_id, user_id, task_metadata)
