# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Additional tests for metadata base classes to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fundamental.metadata.base import MetadataProvider
from fundamental.models.metadata import MetadataRecord, MetadataSourceInfo

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
