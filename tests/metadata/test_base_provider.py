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

"""Additional tests for metadata base classes to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bookcard.metadata.base import MetadataProvider
from bookcard.models.metadata import MetadataRecord, MetadataSourceInfo

if TYPE_CHECKING:
    from collections.abc import Sequence


class ConcreteMetadataProvider(MetadataProvider):
    """Concrete implementation for testing."""

    def get_source_info(self) -> MetadataSourceInfo:
        """Get source info."""
        return MetadataSourceInfo(
            id="test",
            name="Test Provider",
            description="Test",
            base_url="https://test.com",
        )

    def search(
        self, query: str, locale: str = "en", max_results: int = 10
    ) -> Sequence[MetadataRecord]:
        """Search implementation."""
        return []


def test_metadata_provider_init_with_enabled() -> None:
    """Test MetadataProvider __init__ with enabled=True (covers line 62)."""
    provider = ConcreteMetadataProvider(enabled=True)
    assert provider.enabled is True


def test_metadata_provider_init_with_disabled() -> None:
    """Test MetadataProvider __init__ with enabled=False (covers line 62)."""
    provider = ConcreteMetadataProvider(enabled=False)
    assert provider.enabled is False


def test_metadata_provider_is_enabled() -> None:
    """Test MetadataProvider is_enabled method (covers line 112)."""
    provider = ConcreteMetadataProvider(enabled=True)
    assert provider.is_enabled() is True

    provider.enabled = False
    assert provider.is_enabled() is False


def test_metadata_provider_set_enabled() -> None:
    """Test MetadataProvider set_enabled method (covers line 122)."""
    provider = ConcreteMetadataProvider(enabled=True)

    provider.set_enabled(False)
    assert provider.enabled is False

    provider.set_enabled(True)
    assert provider.enabled is True
