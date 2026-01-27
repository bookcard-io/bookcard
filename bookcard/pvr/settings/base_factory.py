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

"""Base settings factory for PVR system.

This module provides a generic settings factory class following DRY
principles by reducing repetitive settings creation code.
"""

from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class SettingsFactory:
    """Generic settings factory for creating settings from definitions.

    This factory class reduces code duplication by providing a generic
    way to create settings objects with common fields and optional
    extra fields from additional_settings.

    Parameters
    ----------
    settings_class : type[T]
        Settings class to instantiate.
    extra_fields : dict[str, tuple[str, Any]] | None
        Mapping of settings field names to (source_key, default_value) tuples.
        source_key is the key in additional_settings, default_value is used
        if the key is not found.

    Examples
    --------
    >>> from bookcard.pvr.base import (
    ...     DownloadClientSettings,
    ... )
    >>> class MySettings(
    ...     DownloadClientSettings
    ... ):
    ...     url_base: (
    ...         str | None
    ...     ) = None
    >>> factory = SettingsFactory(
    ...     MySettings,
    ...     {
    ...         "url_base": (
    ...             "url_base",
    ...             None,
    ...         )
    ...     },
    ... )
    >>> settings = (
    ...     factory.create(
    ...         client_def
    ...     )
    ... )
    """

    def __init__(
        self,
        settings_class: type[T],
        extra_fields: dict[str, tuple[str, Any]] | None = None,
    ) -> None:
        """Initialize settings factory.

        Parameters
        ----------
        settings_class : type[T]
            Settings class to instantiate.
        extra_fields : dict[str, tuple[str, Any]] | None
            Extra field mappings.
        """
        self.settings_class = settings_class
        self.extra_fields = extra_fields or {}

    def create(
        self,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        use_ssl: bool,
        timeout_seconds: int,
        category: str | None,
        download_path: str | None,
        additional_settings: dict[str, Any] | None = None,
    ) -> T:
        """Create settings instance.

        Parameters
        ----------
        host : str
            Hostname.
        port : int
            Port number.
        username : str | None
            Username.
        password : str | None
            Password.
        use_ssl : bool
            Whether to use SSL.
        timeout_seconds : int
            Timeout in seconds.
        category : str | None
            Category.
        download_path : str | None
            Download path.
        additional_settings : dict[str, Any] | None
            Additional settings dictionary.

        Returns
        -------
        T
            Settings instance.
        """
        kwargs: dict[str, Any] = {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "use_ssl": use_ssl,
            "timeout_seconds": timeout_seconds,
            "category": category,
            "download_path": download_path,
        }

        # Add extra fields from additional_settings
        for field_name, (source_key, default_value) in self.extra_fields.items():
            if additional_settings:
                value = additional_settings.get(source_key, default_value)
            else:
                value = default_value

            # Convert to appropriate type
            if value is not None:
                kwargs[field_name] = (
                    str(value) if isinstance(default_value, str) else value
                )
            else:
                kwargs[field_name] = default_value

        return self.settings_class(**kwargs)  # ty:ignore[invalid-return-type]


class IndexerSettingsFactory:
    """Generic indexer settings factory.

    Parameters
    ----------
    settings_class : type[T]
        Indexer settings class to instantiate.
    extra_fields : dict[str, tuple[str, Any]] | None
        Extra field mappings.
    """

    def __init__(
        self,
        settings_class: type[T],
        extra_fields: dict[str, tuple[str, Any]] | None = None,
    ) -> None:
        """Initialize indexer settings factory."""
        self.settings_class = settings_class
        self.extra_fields = extra_fields or {}

    def create(
        self,
        base_url: str,
        api_key: str | None,
        timeout_seconds: int,
        retry_count: int,
        categories: list[int] | None,
        additional_settings: dict[str, Any] | None = None,
    ) -> T:
        """Create indexer settings instance.

        Parameters
        ----------
        base_url : str
            Base URL.
        api_key : str | None
            API key.
        timeout_seconds : int
            Timeout in seconds.
        retry_count : int
            Retry count.
        categories : list[int] | None
            Categories.
        additional_settings : dict[str, Any] | None
            Additional settings.

        Returns
        -------
        T
            Settings instance.
        """
        kwargs: dict[str, Any] = {
            "base_url": base_url,
            "api_key": api_key,
            "timeout_seconds": timeout_seconds,
            "retry_count": retry_count,
            "categories": categories,
        }

        # Add extra fields from additional_settings
        for field_name, (source_key, default_value) in self.extra_fields.items():
            if additional_settings:
                value = additional_settings.get(source_key, default_value)
            else:
                value = default_value

            if value is not None:
                kwargs[field_name] = (
                    str(value) if isinstance(default_value, str) else value
                )
            else:
                kwargs[field_name] = default_value

        return self.settings_class(**kwargs)  # ty:ignore[invalid-return-type]
