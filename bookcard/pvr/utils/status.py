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

"""Download status utilities for PVR download clients.

This module provides status enums and mapping utilities, following OCP
by allowing status mapping to be configured without modifying client code.
"""

from collections.abc import Callable
from enum import StrEnum


class DownloadStatus(StrEnum):
    """Download status enumeration.

    Standard status values used across all download clients to replace
    magic strings and ensure consistency.
    """

    COMPLETED = "completed"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    QUEUED = "queued"
    FAILED = "failed"
    SEEDING = "seeding"
    STALLED = "stalled"
    CHECKING = "checking"
    METADATA = "metadata"


class StatusMapper:
    """Maps client-specific status values to standard DownloadStatus.

    This class follows OCP by allowing status mappings to be configured
    and extended without modifying client implementations. Supports both
    static mappings and dynamic rules.

    Parameters
    ----------
    mappings : dict[str | int, str] | None
        Optional initial mapping from client status values to DownloadStatus values.
        Keys can be strings or integers, values should be DownloadStatus enum values.
    default : str
        Default status to return if mapping not found (default: "downloading").

    Examples
    --------
    >>> mapper = StatusMapper({
    ...     "uploading": DownloadStatus.COMPLETED,
    ...     "downloading": DownloadStatus.DOWNLOADING,
    ...     6: DownloadStatus.COMPLETED,
    ... })
    >>> mapper.map(
    ...     "uploading"
    ... )
    'completed'
    >>> mapper.map(6)
    'completed'
    >>> mapper.map(
    ...     "unknown"
    ... )
    'downloading'
    >>> # With rules
    >>> mapper = (
    ...     StatusMapper()
    ... )
    >>> mapper.add_mapping(
    ...     "completed",
    ...     DownloadStatus.COMPLETED,
    ... )
    >>> mapper.add_rule(
    ...     lambda s: (
    ...         DownloadStatus.FAILED
    ...         if "error"
    ...         in str(
    ...             s
    ...         ).lower()
    ...         else None
    ...     )
    ... )
    >>> mapper.map(
    ...     "completed"
    ... )
    'completed'
    >>> mapper.map(
    ...     "error_state"
    ... )
    'failed'
    """

    def __init__(
        self,
        mappings: dict[str | int, str] | None = None,
        default: str = DownloadStatus.DOWNLOADING,
    ) -> None:
        """Initialize status mapper.

        Parameters
        ----------
        mappings : dict[str | int, str] | None
            Optional initial mapping from client status to standard status.
        default : str
            Default status if mapping not found.
        """
        self._mappings: dict[str | int, str] = mappings or {}
        self._default = default
        self._rules: list[Callable[[str | int], str | None]] = []

    def add_mapping(self, key: str | int, status: str) -> "StatusMapper":
        """Add or update a status mapping.

        Parameters
        ----------
        key : str | int
            Client-specific status value.
        status : str
            Standard DownloadStatus value.

        Returns
        -------
        StatusMapper
            Self for method chaining.
        """
        self._mappings[key] = status
        return self

    def add_rule(self, rule: Callable[[str | int], str | None]) -> "StatusMapper":
        """Add a custom mapping rule (checked before mappings).

        Rules are checked in order before static mappings. If a rule
        returns a non-None value, that value is used. Otherwise, the
        next rule or mapping is checked.

        Parameters
        ----------
        rule : Callable[[str | int], str | None]
            Rule function that takes client status and returns standard
            status or None if rule doesn't apply.

        Returns
        -------
        StatusMapper
            Self for method chaining.

        Examples
        --------
        >>> mapper = (
        ...     StatusMapper()
        ... )
        >>> mapper.add_rule(
        ...     lambda s: (
        ...         DownloadStatus.FAILED
        ...         if "error"
        ...         in str(
        ...             s
        ...         ).lower()
        ...         else None
        ...     )
        ... )
        >>> mapper.map(
        ...     "error_state"
        ... )
        'failed'
        """
        self._rules.append(rule)
        return self

    def map(self, client_status: str | int) -> str:
        """Map client status to standard status.

        Checks rules first (in order), then static mappings, then returns default.

        Parameters
        ----------
        client_status : str | int
            Client-specific status value.

        Returns
        -------
        str
            Standard DownloadStatus value.
        """
        # Check rules first
        for rule in self._rules:
            if result := rule(client_status):
                return result

        # Then check static mappings
        return self._mappings.get(client_status, self._default)


class StatusMappingPresets:
    """Predefined status mappings for common client types.

    This class provides reusable status mapping presets following DRY principles
    by centralizing common status mapping patterns used across multiple clients.
    """

    @staticmethod
    def torrent_string_based() -> dict[str, str]:
        """Status mapping for clients using string statuses.

        Returns
        -------
        dict[str, str]
            Mapping from client string statuses to DownloadStatus values.

        Examples
        --------
        >>> mapping = StatusMappingPresets.torrent_string_based()
        >>> mapping["completed"]
        'completed'
        """
        return {
            "completed": DownloadStatus.COMPLETED,
            "seeding": DownloadStatus.COMPLETED,
            "uploading": DownloadStatus.COMPLETED,
            "downloading": DownloadStatus.DOWNLOADING,
            "paused": DownloadStatus.PAUSED,
            "queued": DownloadStatus.QUEUED,
            "error": DownloadStatus.FAILED,
            "failed": DownloadStatus.FAILED,
            "stalled": DownloadStatus.STALLED,
            "checking": DownloadStatus.CHECKING,
            "metadata": DownloadStatus.METADATA,
        }

    @staticmethod
    def transmission_numeric() -> dict[int, str]:
        """Status mapping for Transmission-style numeric statuses.

        Returns
        -------
        dict[int, str]
            Mapping from numeric status codes to DownloadStatus values.

        Examples
        --------
        >>> mapping = StatusMappingPresets.transmission_numeric()
        >>> mapping[0]
        'paused'
        """
        return {
            0: DownloadStatus.PAUSED,
            1: DownloadStatus.QUEUED,
            2: DownloadStatus.CHECKING,
            3: DownloadStatus.QUEUED,
            4: DownloadStatus.DOWNLOADING,
            5: DownloadStatus.QUEUED,
            6: DownloadStatus.COMPLETED,
        }
