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

"""Types for library scan orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class ScanStatus(StrEnum):
    """Known scan status values stored in ``LibraryScanState.scan_status``."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class DataSourceConfig:
    """Scan data source configuration.

    Parameters
    ----------
    name : str
        Data source name (e.g., ``"openlibrary"``).
    kwargs : dict[str, Any]
        Additional configuration passed through to scan workers.
    """

    name: str
    kwargs: dict[str, Any]

    @staticmethod
    def from_metadata(metadata: dict[str, Any]) -> DataSourceConfig:
        """Parse scan data source configuration from task metadata.

        Parameters
        ----------
        metadata : dict[str, Any]
            Task metadata dictionary.

        Returns
        -------
        DataSourceConfig
            Parsed data source config. Defaults to ``openlibrary`` if missing.
        """
        raw = metadata.get("data_source_config")
        if not isinstance(raw, dict):
            return DataSourceConfig(name="openlibrary", kwargs={})

        name = raw.get("name")
        kwargs = raw.get("kwargs")

        if not isinstance(name, str) or not name:
            name = "openlibrary"
        if not isinstance(kwargs, dict):
            kwargs = {}

        return DataSourceConfig(name=name, kwargs=dict(kwargs))

    def to_payload(self) -> dict[str, Any]:
        """Convert to the wire payload structure expected by scan workers.

        Returns
        -------
        dict[str, Any]
            Payload fragment with keys ``name`` and ``kwargs``.
        """
        return {"name": self.name, "kwargs": dict(self.kwargs)}
