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

"""Type definitions for download service."""

from typing import TypedDict


class ClientItemInfo(TypedDict, total=False):
    """Information about a download item from a download client.

    Attributes
    ----------
    client_item_id : str
        Client-specific item identifier.
    progress : float
        Download progress (0.0 to 1.0).
    status : str
        Client-specific status string.
    size_bytes : int
        Total size in bytes.
    downloaded_bytes : int
        Bytes downloaded so far.
    download_speed_bytes_per_sec : float
        Current download speed.
    eta_seconds : int
        Estimated time to completion in seconds.
    file_path : str
        Path to downloaded file(s).
    """

    client_item_id: str
    progress: float
    status: str
    size_bytes: int
    downloaded_bytes: int
    download_speed_bytes_per_sec: float
    eta_seconds: int
    file_path: str
