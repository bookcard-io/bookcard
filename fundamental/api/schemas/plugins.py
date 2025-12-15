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

"""Plugin API schemas."""

from pydantic import BaseModel


class PluginInfo(BaseModel):
    """Schema for installed plugin information."""

    name: str
    version: str
    description: str
    author: str


class PluginInstallRequest(BaseModel):
    """Schema for plugin installation request (from Git)."""

    repo_url: str
    # Optional fields for Git install
    plugin_path: str | None = None  # Subdirectory in repo
    branch: str | None = None


class PluginUrlInstallRequest(BaseModel):
    """Schema for plugin installation request (from URL)."""

    url: str
