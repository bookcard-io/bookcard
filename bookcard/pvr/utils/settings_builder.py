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

"""Settings builder for PVR download clients.

This module provides a fluent builder for creating settings objects,
following DRY principles by reducing boilerplate in settings factories.
"""

from collections.abc import Callable
from typing import Any

from bookcard.models.pvr import DownloadClientDefinition

# Import at runtime to avoid potential circular dependencies
from bookcard.pvr.base import DownloadClientSettings


class SettingsBuilder:
    """Fluent builder for creating settings with validation.

    This class reduces boilerplate in settings factories by providing
    a fluent interface for building settings objects.

    Parameters
    ----------
    settings_class : type[DownloadClientSettings]
        Settings class to instantiate.

    Examples
    --------
    >>> from bookcard.pvr.download_clients.qbittorrent import (
    ...     QBittorrentSettings,
    ... )
    >>> builder = SettingsBuilder(
    ...     QBittorrentSettings
    ... )
    >>> settings = (
    ...     builder
    ...     .with_base_fields(
    ...         client_def
    ...     )
    ...     .with_optional(
    ...         "url_base",
    ...         client_def.additional_settings
    ...         or {},
    ...     )
    ...     .build()
    ... )
    """

    def __init__(self, settings_class: type[DownloadClientSettings]) -> None:
        """Initialize settings builder.

        Parameters
        ----------
        settings_class : type[DownloadClientSettings]
            Settings class to instantiate.
        """
        self._class = settings_class
        self._fields: dict[str, Any] = {}

    def with_base_fields(
        self, client_def: DownloadClientDefinition
    ) -> "SettingsBuilder":
        """Add base fields from client definition.

        Parameters
        ----------
        client_def : DownloadClientDefinition
            Client definition containing base fields.

        Returns
        -------
        SettingsBuilder
            Self for method chaining.
        """
        self._fields.update({
            "host": client_def.host,
            "port": client_def.port,
            "username": client_def.username,
            "password": client_def.password,
            "use_ssl": client_def.use_ssl,
            "timeout_seconds": client_def.timeout_seconds,
            "category": client_def.category,
            "download_path": client_def.download_path,
        })
        return self

    def with_optional(
        self,
        field_name: str,
        source_dict: dict[str, Any] | None,
        default: Any = None,  # noqa: ANN401
        transform: Callable[[Any], Any] | None = None,
    ) -> "SettingsBuilder":
        """Add optional field from source dictionary.

        Parameters
        ----------
        field_name : str
            Field name in both source dict and settings class.
        source_dict : dict[str, Any] | None
            Source dictionary to read from.
        default : Any
            Default value if field not in source dict (default: None).
        transform : Callable[[Any], Any] | None
            Optional transformation function to apply to value.

        Returns
        -------
        SettingsBuilder
            Self for method chaining.
        """
        if source_dict is None:
            if default is not None:
                self._fields[field_name] = default
            return self

        value = source_dict.get(field_name, default)

        if value is not None and transform is not None:
            value = transform(value)

        if value is not None:
            self._fields[field_name] = value

        return self

    def with_field(self, field_name: str, value: Any) -> "SettingsBuilder":  # noqa: ANN401
        """Add field directly.

        Parameters
        ----------
        field_name : str
            Field name.
        value : Any
            Field value.

        Returns
        -------
        SettingsBuilder
            Self for method chaining.
        """
        self._fields[field_name] = value
        return self

    def build(self) -> DownloadClientSettings:
        """Build settings instance.

        Returns
        -------
        DownloadClientSettings
            Settings instance.

        Raises
        ------
        ValueError
            If required fields are missing or validation fails.
        """
        return self._class(**self._fields)
