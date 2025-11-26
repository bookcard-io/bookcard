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

"""Data source registry for managing available data sources."""

from collections.abc import Sequence

from fundamental.services.library_scanning.data_sources.base import BaseDataSource
from fundamental.services.library_scanning.data_sources.hardcover import (
    HardcoverDataSource,
)
from fundamental.services.library_scanning.data_sources.openlibrary import (
    OpenLibraryDataSource,
)
from fundamental.services.library_scanning.data_sources.openlibrary_dump import (
    OpenLibraryDumpDataSource,
)

_DATA_SOURCES: dict[str, type[BaseDataSource]] = {
    "openlibrary": OpenLibraryDataSource,
    "openlibrary_dump": OpenLibraryDumpDataSource,
    "hardcover": HardcoverDataSource,
}


class DataSourceRegistry:
    """Registry for managing available data sources.

    Provides dependency injection point for selecting data sources.
    Supports multiple sources, single source, or source-specific matching.
    """

    @classmethod
    def get_available_sources(cls) -> list[str]:
        """Get list of available data source names.

        Returns
        -------
        list[str]
            List of data source names.
        """
        return list(_DATA_SOURCES.keys())

    @classmethod
    def create_source(
        cls,
        source_name: str,
        **kwargs: object,
    ) -> BaseDataSource:
        """Create a data source instance by name.

        Parameters
        ----------
        source_name : str
            Name of the data source (e.g., "openlibrary").
        **kwargs : object
            Additional arguments to pass to data source constructor.

        Returns
        -------
        BaseDataSource
            Data source instance.

        Raises
        ------
        ValueError
            If source name is not recognized.
        """
        source_class = _DATA_SOURCES.get(source_name.lower())
        if source_class is None:
            available = ", ".join(cls.get_available_sources())
            error_msg = f"Unknown data source: {source_name}. Available: {available}"
            raise ValueError(error_msg)

        return source_class(**kwargs)

    @classmethod
    def create_sources(
        cls,
        source_names: Sequence[str] | None = None,
        **kwargs: object,
    ) -> list[BaseDataSource]:
        """Create multiple data source instances.

        Parameters
        ----------
        source_names : Sequence[str] | None
            List of data source names. If None, creates all available sources.
        **kwargs : object
            Additional arguments to pass to data source constructors.

        Returns
        -------
        list[BaseDataSource]
            List of data source instances.
        """
        if source_names is None:
            source_names = cls.get_available_sources()

        return [cls.create_source(name, **kwargs) for name in source_names]

    @classmethod
    def register_source(
        cls,
        name: str,
        source_class: type[BaseDataSource],
    ) -> None:
        """Register a new data source class.

        Parameters
        ----------
        name : str
            Name to register the source under.
        source_class : type[BaseDataSource]
            Data source class to register.
        """
        _DATA_SOURCES[name.lower()] = source_class
