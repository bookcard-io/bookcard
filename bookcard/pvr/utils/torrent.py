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

"""Torrent utility functions for PVR system.

This module provides shared torrent-related utilities following DRY principles
by centralizing duplicate torrent handling logic.
"""


def extract_hash_from_magnet(magnet_url: str) -> str | None:
    """Extract info hash from magnet link.

    Parameters
    ----------
    magnet_url : str
        Magnet link URL.

    Returns
    -------
    str | None
        Extracted hash in uppercase, or None if not found.

    Examples
    --------
    >>> extract_hash_from_magnet(
    ...     "magnet:?xt=urn:btih:ABC123DEF456"
    ... )
    'ABC123DEF456'
    >>> extract_hash_from_magnet(
    ...     "magnet:?xt=urn:btih:abc123&dn=example"
    ... )
    'ABC123'
    """
    for part in magnet_url.split("&"):
        if part.startswith("xt=urn:btih:"):
            return part.split(":")[-1].upper()
    return None
