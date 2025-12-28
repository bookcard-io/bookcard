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

"""Models for Prowlarr sync operations."""

from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass
class SyncStatistics:
    """Statistics for sync operation."""

    added: int = 0
    updated: int = 0
    removed: int = 0
    errors: int = 0

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary."""
        return {
            "added": self.added,
            "updated": self.updated,
            "removed": self.removed,
            "errors": self.errors,
        }


class ProwlarrIndexerResponse(BaseModel):
    """Prowlarr indexer response model."""

    id: int
    name: str
    protocol: str
    enable: bool = Field(default=False, alias="enable")
    priority: int = 0
    urls: dict[str, str] | None = None  # Some versions might expose urls

    class Config:
        """Pydantic config."""

        populate_by_name = True
        extra = "allow"
