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

"""Client health management service.

Manages download client health status updates, following SRP.
"""

from sqlmodel import Session

from bookcard.common.clock import Clock, UTCClock
from bookcard.models.pvr import DownloadClientDefinition, DownloadClientStatus


class ClientHealthManager:
    """Manages client status and health checks."""

    def __init__(self, session: Session, clock: Clock | None = None) -> None:
        """Initialize health manager.

        Parameters
        ----------
        session : Session
            Database session.
        clock : Clock | None
            Time provider.
        """
        self._session = session
        self._clock = clock or UTCClock()

    def update_status(
        self,
        client: DownloadClientDefinition,
        status: DownloadClientStatus,
        error_message: str | None = None,
    ) -> None:
        """Update client health status.

        Parameters
        ----------
        client : DownloadClientDefinition
            Client to update.
        status : DownloadClientStatus
            New status.
        error_message : str | None
            Error message if unhealthy.
        """
        client.status = status
        client.last_checked_at = self._clock.now()

        if status == DownloadClientStatus.HEALTHY:
            client.last_successful_connection_at = self._clock.now()
            client.error_count = 0
            client.error_message = None
        else:
            client.error_count += 1
            client.error_message = error_message

        self._session.add(client)
        # We don't commit here to allow transaction grouping by caller
