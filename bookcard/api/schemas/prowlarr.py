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

"""Prowlarr configuration schemas."""

from pydantic import BaseModel


class ProwlarrConfigBase(BaseModel):
    """Base schema for Prowlarr configuration."""

    url: str = "http://localhost:9696"
    api_key: str | None = None
    enabled: bool = False
    sync_categories: list[str] | None = None
    sync_app_profiles: list[int] | None = None
    sync_interval_minutes: int = 60


class ProwlarrConfigCreate(ProwlarrConfigBase):
    """Schema for creating Prowlarr configuration."""


class ProwlarrConfigUpdate(ProwlarrConfigBase):
    """Schema for updating Prowlarr configuration."""


class ProwlarrConfigRead(ProwlarrConfigBase):
    """Schema for reading Prowlarr configuration."""

    id: int

    class Config:
        """Pydantic configuration."""

        from_attributes = True
