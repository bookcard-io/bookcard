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

"""Message publisher for scan jobs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from redis.exceptions import RedisError

from bookcard.services.library_scanning.workers.progress import JobProgressTracker
from bookcard.services.messaging.redis_broker import RedisBroker
from bookcard.services.tasks.library_scan.errors import ScanDispatchError

if TYPE_CHECKING:
    from bookcard.models.config import Library
    from bookcard.services.messaging.base import MessagePublisher
    from bookcard.services.tasks.library_scan.types import DataSourceConfig


@dataclass(frozen=True, slots=True)
class ScanJob:
    """A scan job payload to be dispatched to distributed scan workers.

    Parameters
    ----------
    task_id : int
        Task ID for linking distributed workers back to the unified task record.
    library : Library
        Library to scan.
    data_source_config : DataSourceConfig
        Data source configuration forwarded to workers.
    """

    task_id: int
    library: Library
    data_source_config: DataSourceConfig

    def to_payload(self) -> dict[str, Any]:
        """Build payload matching the scan workers' expected schema."""
        return {
            "task_id": self.task_id,
            "library_id": self.library.id,
            "calibre_db_path": self.library.calibre_db_path,
            "calibre_db_file": self.library.calibre_db_file or "metadata.db",
            "data_source_config": self.data_source_config.to_payload(),
        }


class ScanJobPublisher:
    """Publishes scan jobs to the distributed scan pipeline.

    Parameters
    ----------
    publisher : MessagePublisher
        Publisher used to enqueue scan jobs.
    topic : str, optional
        Topic/queue name for scan jobs.
    """

    def __init__(
        self, publisher: MessagePublisher, *, topic: str = "scan_jobs"
    ) -> None:
        self._publisher = publisher
        self._topic = topic

    def clear_previous_progress(self, library_id: int) -> None:
        """Clear progress keys for a library if supported by the broker.

        Parameters
        ----------
        library_id : int
            Library identifier.
        """
        if isinstance(self._publisher, RedisBroker):
            JobProgressTracker(self._publisher).clear_job(library_id)

    def publish(self, job: ScanJob) -> None:
        """Publish a scan job.

        Parameters
        ----------
        job : ScanJob
            Job to publish.

        Raises
        ------
        ScanDispatchError
            If the job cannot be dispatched.
        """
        try:
            self._publisher.publish(self._topic, job.to_payload())
        except RedisError as exc:
            raise ScanDispatchError(str(exc)) from exc
        except ValueError as exc:
            # Some publishers may validate payload/connection params.
            raise ScanDispatchError(str(exc)) from exc
