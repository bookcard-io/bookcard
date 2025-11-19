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

"""Tests for data source registry to achieve 100% coverage."""

import pytest

from fundamental.services.library_scanning.data_sources.base import BaseDataSource
from fundamental.services.library_scanning.data_sources.registry import (
    DataSourceRegistry,
)


def test_get_available_sources() -> None:
    """Test get_available_sources returns list of source names."""
    sources = DataSourceRegistry.get_available_sources()
    assert isinstance(sources, list)
    assert "openlibrary" in sources


def test_create_source_valid() -> None:
    """Test create_source with valid source name."""
    source = DataSourceRegistry.create_source("openlibrary")
    assert isinstance(source, BaseDataSource)


def test_create_source_invalid() -> None:
    """Test create_source with invalid source name."""
    with pytest.raises(ValueError, match="Unknown data source"):
        DataSourceRegistry.create_source("invalid_source")


def test_create_source_case_insensitive() -> None:
    """Test create_source is case insensitive."""
    source = DataSourceRegistry.create_source("OpenLibrary")
    assert isinstance(source, BaseDataSource)


def test_create_sources_with_names() -> None:
    """Test create_sources with specific source names."""
    sources = DataSourceRegistry.create_sources(["openlibrary"])
    assert len(sources) == 1
    assert isinstance(sources[0], BaseDataSource)


def test_create_sources_none() -> None:
    """Test create_sources with None (creates all available)."""
    sources = DataSourceRegistry.create_sources()
    assert len(sources) > 0
    assert all(isinstance(s, BaseDataSource) for s in sources)


def test_create_sources_with_kwargs() -> None:
    """Test create_sources passes kwargs to constructors."""
    # OpenLibraryDataSource accepts: base_url, timeout, rate_limit_delay
    sources = DataSourceRegistry.create_sources(
        ["openlibrary"], timeout=60.0, rate_limit_delay=1.0
    )
    assert len(sources) == 1


def test_register_source() -> None:
    """Test register_source adds new source."""
    from collections.abc import Sequence

    from fundamental.services.library_scanning.data_sources.types import (
        AuthorData,
        BookData,
        IdentifierDict,
    )

    # Create a real class that extends BaseDataSource for testing
    class TestDataSource(BaseDataSource):
        @property
        def name(self) -> str:
            return "test_source"

        def search_author(
            self, name: str, identifiers: IdentifierDict | None = None
        ) -> Sequence[AuthorData]:
            return []

        def get_author(self, key: str) -> AuthorData | None:
            return None

        def search_book(
            self,
            title: str | None = None,
            isbn: str | None = None,
            authors: list[str] | None = None,
        ) -> Sequence[BookData]:
            return []

        def get_book(self, key: str, skip_authors: bool = False) -> BookData | None:
            return None

    # Register new source
    DataSourceRegistry.register_source("test_source", TestDataSource)

    # Verify it's available
    sources = DataSourceRegistry.get_available_sources()
    assert "test_source" in sources

    # Verify we can create it
    source = DataSourceRegistry.create_source("test_source")
    assert source is not None
    assert isinstance(source, TestDataSource)

    # Cleanup: remove test source (restore original state)
    from fundamental.services.library_scanning.data_sources.registry import (
        _DATA_SOURCES,
    )

    if "test_source" in _DATA_SOURCES:
        del _DATA_SOURCES["test_source"]


def test_register_source_case_insensitive() -> None:
    """Test register_source stores name in lowercase."""
    from collections.abc import Sequence

    from fundamental.services.library_scanning.data_sources.types import (
        AuthorData,
        BookData,
        IdentifierDict,
    )

    # Create a real class that extends BaseDataSource for testing
    class TestDataSource2(BaseDataSource):
        @property
        def name(self) -> str:
            return "test_source2"

        def search_author(
            self, name: str, identifiers: IdentifierDict | None = None
        ) -> Sequence[AuthorData]:
            return []

        def get_author(self, key: str) -> AuthorData | None:
            return None

        def search_book(
            self,
            title: str | None = None,
            isbn: str | None = None,
            authors: list[str] | None = None,
        ) -> Sequence[BookData]:
            return []

        def get_book(self, key: str, skip_authors: bool = False) -> BookData | None:
            return None

    DataSourceRegistry.register_source("TestSource", TestDataSource2)

    # Should be accessible with lowercase
    sources = DataSourceRegistry.get_available_sources()
    assert "testsource" in sources

    # Cleanup
    from fundamental.services.library_scanning.data_sources.registry import (
        _DATA_SOURCES,
    )

    if "testsource" in _DATA_SOURCES:
        del _DATA_SOURCES["testsource"]
