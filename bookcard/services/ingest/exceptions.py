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

"""Domain-specific exceptions for ingest operations.

Follows LSP by providing consistent exception types.
"""


class IngestError(Exception):
    """Base exception for ingest operations."""


class IngestHistoryNotFoundError(IngestError):
    """Raised when ingest history record not found.

    Parameters
    ----------
    history_id : int
        The history ID that was not found.
    """

    def __init__(self, history_id: int) -> None:
        """Initialize exception.

        Parameters
        ----------
        history_id : int
            The history ID that was not found.
        """
        super().__init__(f"Ingest history {history_id} not found")
        self.history_id = history_id


class IngestHistoryCreationError(IngestError):
    """Raised when history record creation fails."""
