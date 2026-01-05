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

import contextlib
import hashlib
from typing import Any


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
        if "xt=urn:btih:" in part:
            # Handle both "xt=urn:btih:hash" and "magnet:?xt=urn:btih:hash"
            if part.startswith("xt=urn:btih:"):
                return part.split(":")[-1].upper()
            # Handle "magnet:?xt=urn:btih:hash" format
            idx = part.find("xt=urn:btih:")
            if idx != -1:
                return part[idx + len("xt=urn:btih:") :].upper()
    return None


def _decode_bencode(data: bytes) -> tuple[Any, int]:
    """Decode single bencoded value."""
    char = data[0:1]
    if char == b"i":
        end = data.index(b"e")
        return int(data[1:end]), end + 1
    if char == b"l":
        lst = []
        offset = 1
        while data[offset : offset + 1] != b"e":
            val, used = _decode_bencode(data[offset:])
            lst.append(val)
            offset += used
        return lst, offset + 1
    if char == b"d":
        dct = {}
        offset = 1
        while data[offset : offset + 1] != b"e":
            key, used = _decode_bencode(data[offset:])
            val, used_val = _decode_bencode(data[offset + used :])
            dct[key.decode("utf-8") if isinstance(key, bytes) else key] = val
            offset += used + used_val
        return dct, offset + 1
    if char.isdigit():
        colon = data.index(b":")
        length = int(data[:colon])
        return data[colon + 1 : colon + 1 + length], colon + 1 + length

    # If we encounter something invalid, we might be at the end or it's malformed
    # For our purpose (finding info dict), strict validation isn't strictly necessary
    # but let's be safe.
    msg = f"Invalid bencode start: {char!r}"
    raise ValueError(msg)


def _encode_bencode(data: Any) -> bytes:  # noqa: ANN401
    """Encode value to bencode."""
    if isinstance(data, int):
        return f"i{data}e".encode()
    if isinstance(data, bytes):
        return f"{len(data)}:".encode() + data
    if isinstance(data, str):
        b = data.encode("utf-8")
        return f"{len(b)}:".encode() + b
    if isinstance(data, list):
        return b"l" + b"".join(_encode_bencode(x) for x in data) + b"e"
    if isinstance(data, dict):
        # Keys must be sorted strings/bytes
        items = sorted(
            data.items(),
            key=lambda x: x[0] if isinstance(x[0], bytes) else x[0].encode("utf-8"),
        )
        return (
            b"d"
            + b"".join(_encode_bencode(k) + _encode_bencode(v) for k, v in items)
            + b"e"
        )

    msg = f"Cannot bencode type: {type(data)}"
    raise TypeError(msg)


def calculate_torrent_hash(file_content: bytes) -> str | None:
    """Calculate SHA1 hash of torrent info dictionary.

    Parameters
    ----------
    file_content : bytes
        Raw content of the .torrent file.

    Returns
    -------
    str | None
        Calculated hash (uppercase hex), or None if parsing fails.
    """
    with contextlib.suppress(Exception):
        decoded, _ = _decode_bencode(file_content)
        if isinstance(decoded, dict) and "info" in decoded:
            info_dict = decoded["info"]
            encoded_info = _encode_bencode(info_dict)
            return hashlib.sha1(encoded_info).hexdigest().upper()  # noqa: S324
    return None
