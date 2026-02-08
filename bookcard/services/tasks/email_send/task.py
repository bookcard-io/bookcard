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

"""Email send task implementation.

Refactored to follow SOLID principles with dependency injection,
value objects, and separation of concerns.
"""

import logging
from typing import Any

from bookcard.services.tasks.base import BaseTask
from bookcard.services.tasks.context import WorkerContext
from bookcard.services.tasks.email_send.dependencies import EmailSendDependencies
from bookcard.services.tasks.email_send.domain import SendBookRequest, SendMetadata
from bookcard.services.tasks.email_send.exceptions import TaskCancelledError
from bookcard.services.tasks.email_send.preprocessing import PreprocessingContext
from bookcard.services.tasks.email_send.progress import ProgressTracker
from bookcard.services.tasks.email_send.wiring import (
    create_default_email_send_dependencies,
)

logger = logging.getLogger(__name__)


class EmailSendTask(BaseTask):
    """Task for sending a book via email.

    Refactored to use dependency injection, eliminating Service Locator
    anti-pattern and improving testability.
    """

    def __init__(
        self,
        task_id: int,
        user_id: int,
        metadata: dict[str, Any],
        dependencies: EmailSendDependencies | None = None,
    ) -> None:
        """Initialize email send task.

        Parameters
        ----------
        task_id : int
            Database task ID.
        user_id : int
            User ID creating the task.
        metadata : dict[str, Any]
            Task metadata containing book_id, to_email, file_format, encryption_key.
        dependencies : EmailSendDependencies | None
            Optional dependencies container. If None, will be created from metadata
            during execution (requires session).

        Raises
        ------
        ValueError
            If required metadata fields are missing or invalid.
        TypeError
            If metadata types are incorrect.
        """
        super().__init__(task_id, user_id, metadata)
        self._request = SendBookRequest.from_metadata(metadata)
        self._dependencies = dependencies

    def _check_cancellation(self) -> None:
        """Check if task is cancelled and raise exception if so.

        Raises
        ------
        TaskCancelledError
            If task has been cancelled.
        """
        if self.check_cancelled():
            raise TaskCancelledError(self.task_id)

    def run(self, worker_context: WorkerContext | dict[str, Any]) -> None:
        """Execute email send task.

        Parameters
        ----------
        worker_context : WorkerContext | dict[str, Any]
            Worker context containing session, task_service, update_progress.
            Can be a `WorkerContext` (preferred) or a dict (backward compatibility
            with older runners).

        Raises
        ------
        TaskCancelledError
            If task is cancelled.
        LibraryNotConfiguredError
            If no active library is configured.
        EmailServerNotConfiguredError
            If email server is not configured.
        BookNotFoundError
            If book is not found.
        """
        # Convert legacy dict context to WorkerContext for type safety.
        if isinstance(worker_context, dict):
            context = WorkerContext(
                session=worker_context["session"],
                update_progress=worker_context["update_progress"],
                task_service=worker_context["task_service"],
                enqueue_task=worker_context.get("enqueue_task"),  # type: ignore[arg-type]
            )
        else:
            context = worker_context

        try:
            self._execute(context)
        except TaskCancelledError:
            logger.info("Task %s cancelled", self.task_id)
            # Don't re-raise - cancellation is expected
        except Exception:
            logger.exception("Task %s failed", self.task_id)
            raise

    def _execute(self, context: WorkerContext) -> None:
        """Core execution workflow.

        Parameters
        ----------
        context : WorkerContext
            Worker context.

        Raises
        ------
        TaskCancelledError
            If task is cancelled.
        LibraryNotConfiguredError
            If no active library is configured.
        EmailServerNotConfiguredError
            If email server is not configured.
        BookNotFoundError
            If book is not found.
        """
        # Create dependencies if not provided
        if self._dependencies is None:
            self._dependencies = create_default_email_send_dependencies(
                context.session, self._request.encryption_key.value
            )

        deps = self._dependencies

        # Create progress tracker
        tracker = ProgressTracker(
            callback=context.update_progress,
            total_steps=6,
            check_cancellation=self._check_cancellation,
        )

        # Load library
        tracker.advance("Loading library configuration")
        library = deps.library_provider.get_active_library(
            context.session,
            metadata=self.metadata,
            user_id=self.user_id,
        )

        # Configure email service
        tracker.advance("Configuring email service")
        email_service = deps.email_service_factory.create(
            context.session, self._request.encryption_key.value
        )

        # Create book service
        tracker.advance("Preparing book service")
        book_service = deps.book_service_factory.create(library, context.session)

        # Prepare send
        tracker.advance("Preparing book for send")
        prepared = deps.preparation_service.prepare(
            self._request,
            book_service,
            context.session,
            self.user_id,
        )

        # Run preprocessing
        tracker.advance("Running preprocessing")
        preprocessing_context = PreprocessingContext(
            session=context.session,
            library=library,
            book_with_rels=prepared.book_with_rels,
            book_id=self._request.book_id.value,
            user_id=self.user_id,
            resolved_format=prepared.resolved_format,
            check_cancellation=self._check_cancellation,
        )
        deps.preprocessing_pipeline.execute(preprocessing_context)

        # Send book
        tracker.advance("Sending book")
        book_service.send_book(
            book_id=self._request.book_id.value,
            user_id=self.user_id,
            email_service=email_service,
            to_email=self._request.email_target.address,
            file_format=prepared.resolved_format,
        )

        # Store completion metadata
        send_metadata = SendMetadata(
            book_title=prepared.book_title,
            attachment_filename=prepared.attachment_filename,
        )
        self.set_metadata("book_title", send_metadata.book_title)
        self.set_metadata("attachment_filename", send_metadata.attachment_filename)

        logger.info(
            "Task %s: Book %s sent successfully to %s",
            self.task_id,
            self._request.book_id.value,
            self._request.email_target,
        )
