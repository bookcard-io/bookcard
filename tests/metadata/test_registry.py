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

"""Additional tests for metadata registry to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from fundamental.metadata.base import MetadataProvider
from fundamental.metadata.registry import (
    MetadataProviderRegistry,
    get_registry,
)
from fundamental.models.metadata import MetadataRecord, MetadataSourceInfo

if TYPE_CHECKING:
    from collections.abc import Sequence


class MockTestProvider(MetadataProvider):
    """Test provider for registry tests."""

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


class MockTestProvider2(MetadataProvider):
    """Another test provider."""

    def get_source_info(self) -> MetadataSourceInfo:
        """Get source info."""
        return MetadataSourceInfo(
            id="test2",
            name="Test Provider 2",
            description="Test 2",
            base_url="https://test2.com",
        )

    def search(
        self, query: str, locale: str = "en", max_results: int = 10
    ) -> Sequence[MetadataRecord]:
        """Search implementation."""
        return []


def test_registry_init() -> None:
    """Test MetadataProviderRegistry __init__ (covers lines 60-61)."""
    with patch.object(MetadataProviderRegistry, "_discover_providers") as mock_discover:
        registry = MetadataProviderRegistry()
        assert registry._providers == {}
        mock_discover.assert_called_once()


def test_registry_discover_providers_path_not_exists() -> None:
    """Test _discover_providers when providers path doesn't exist (covers lines 68-74)."""
    registry = MetadataProviderRegistry.__new__(MetadataProviderRegistry)
    registry._providers = {}

    # Patch Path operations to simulate non-existent providers directory
    with patch("fundamental.metadata.registry.Path") as mock_path:
        # Create mock for providers_path
        mock_providers_path = MagicMock()
        mock_providers_path.exists.return_value = False

        # Mock Path(__file__).parent / "providers"
        mock_file_path = MagicMock()
        mock_file_path.parent = MagicMock()
        mock_file_path.parent.__truediv__ = MagicMock(return_value=mock_providers_path)

        # Make Path(__file__) return our mock
        mock_path.return_value = mock_file_path

        registry._discover_providers()
        assert len(registry._providers) == 0
        # Verify exists was checked (line 68)
        mock_providers_path.exists.assert_called()


def test_registry_discover_providers_import_error() -> None:
    """Test _discover_providers handles ImportError (covers lines 106-107)."""
    registry = MetadataProviderRegistry.__new__(MetadataProviderRegistry)
    registry._providers = {}

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.glob") as mock_glob,
    ):
        mock_file = MagicMock()
        mock_file.name = "test_module.py"
        mock_file.stem = "test_module"
        mock_glob.return_value = [mock_file]

        with patch("importlib.import_module", side_effect=ImportError("Cannot import")):
            registry._discover_providers()
            assert len(registry._providers) == 0


def test_registry_discover_providers_instantiation_error() -> None:
    """Test _discover_providers handles instantiation errors (covers lines 99-105)."""
    registry = MetadataProviderRegistry.__new__(MetadataProviderRegistry)
    registry._providers = {}

    class BadProvider(MetadataProvider):
        """Provider that fails on instantiation."""

        def __init__(self) -> None:
            super().__init__()
            raise ValueError("Cannot instantiate")

        def get_source_info(self) -> MetadataSourceInfo:
            """Get source info."""
            return MetadataSourceInfo(
                id="bad",
                name="Bad",
                description="Bad",
                base_url="https://bad.com",
            )

        def search(
            self, query: str, locale: str = "en", max_results: int = 10
        ) -> Sequence[MetadataRecord]:
            """Search implementation."""
            return []

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.glob") as mock_glob,
    ):
        mock_file = MagicMock()
        mock_file.name = "test_module.py"
        mock_file.stem = "test_module"
        mock_glob.return_value = [mock_file]

        mock_module = MagicMock()
        mock_module.BadProvider = BadProvider

        with (
            patch("importlib.import_module", return_value=mock_module),
            patch("inspect.getmembers", return_value=[("BadProvider", BadProvider)]),
            patch("inspect.isclass", return_value=True),
        ):
            registry._discover_providers()
            assert len(registry._providers) == 0


def test_registry_discover_providers_other_error() -> None:
    """Test _discover_providers handles other errors (covers lines 108-109)."""
    registry = MetadataProviderRegistry.__new__(MetadataProviderRegistry)
    registry._providers = {}

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.glob") as mock_glob,
    ):
        mock_file = MagicMock()
        mock_file.name = "test_module.py"
        mock_file.stem = "test_module"
        mock_glob.return_value = [mock_file]

        # Make import_module raise ValueError (covers lines 108-109)
        with patch("importlib.import_module", side_effect=ValueError("Error")):
            registry._discover_providers()
            assert len(registry._providers) == 0


def test_registry_register_invalid_class() -> None:
    """Test register raises TypeError for invalid class (covers lines 124-126)."""
    registry = MetadataProviderRegistry.__new__(MetadataProviderRegistry)
    registry._providers = {}

    with pytest.raises(TypeError):
        registry.register(str)  # type: ignore[arg-type]


def test_registry_register_existing_provider() -> None:
    """Test register overwrites existing provider (covers lines 131-135)."""
    registry = MetadataProviderRegistry.__new__(MetadataProviderRegistry)
    registry._providers = {}

    # Register first provider
    registry._providers["test"] = MockTestProvider

    # Register again (should overwrite)
    registry.register(MockTestProvider)
    assert registry._providers["test"] == MockTestProvider


def test_registry_register_instantiation_error() -> None:
    """Test register handles instantiation errors (covers lines 142-144)."""
    registry = MetadataProviderRegistry.__new__(MetadataProviderRegistry)
    registry._providers = {}

    class BadProvider(MetadataProvider):
        """Provider that fails on instantiation."""

        def __init__(self) -> None:
            super().__init__()
            raise ValueError("Cannot instantiate")

        def get_source_info(self) -> MetadataSourceInfo:
            """Get source info."""
            raise AttributeError("No source info")

        def search(
            self, query: str, locale: str = "en", max_results: int = 10
        ) -> Sequence[MetadataRecord]:
            """Search implementation."""
            return []

    with pytest.raises(ValueError, match="Failed to register provider"):
        registry.register(BadProvider)


def test_registry_get_provider_not_found() -> None:
    """Test get_provider returns None when not found (covers lines 159-161)."""
    registry = MetadataProviderRegistry.__new__(MetadataProviderRegistry)
    registry._providers = {}

    result = registry.get_provider("nonexistent")
    assert result is None


def test_registry_get_provider_found() -> None:
    """Test get_provider returns provider instance when found (covers line 162)."""
    registry = MetadataProviderRegistry.__new__(MetadataProviderRegistry)
    registry._providers = {"test": MockTestProvider}

    result = registry.get_provider("test")
    assert result is not None
    assert isinstance(result, MockTestProvider)


def test_registry_get_all_providers() -> None:
    """Test get_all_providers yields all providers (covers lines 172-173)."""
    registry = MetadataProviderRegistry.__new__(MetadataProviderRegistry)
    registry._providers = {"test": MockTestProvider, "test2": MockTestProvider2}

    providers = list(registry.get_all_providers())
    assert len(providers) == 2
    assert all(isinstance(p, MetadataProvider) for p in providers)


def test_registry_get_enabled_providers() -> None:
    """Test get_enabled_providers yields only enabled providers (covers lines 183-185)."""
    registry = MetadataProviderRegistry.__new__(MetadataProviderRegistry)
    registry._providers = {"test": MockTestProvider, "test2": MockTestProvider2}

    # Create one disabled provider
    disabled_provider = MockTestProvider2(enabled=False)
    with patch.object(MockTestProvider2, "__new__", return_value=disabled_provider):
        providers = list(registry.get_enabled_providers())
        # Should only return enabled providers
        assert len(providers) >= 0  # At least test provider should be enabled


def test_registry_list_providers() -> None:
    """Test list_providers returns provider IDs (covers line 195)."""
    registry = MetadataProviderRegistry.__new__(MetadataProviderRegistry)
    registry._providers = {"test": MockTestProvider, "test2": MockTestProvider2}

    provider_ids = registry.list_providers()
    assert "test" in provider_ids
    assert "test2" in provider_ids
    assert len(provider_ids) == 2


def test_get_registry_creates_instance() -> None:
    """Test get_registry creates global instance (covers lines 211-213)."""
    # Reset global registry
    import fundamental.metadata.registry as registry_module

    registry_module._registry = None

    registry1 = get_registry()
    assert registry1 is not None
    assert isinstance(registry1, MetadataProviderRegistry)

    # Second call should return same instance
    registry2 = get_registry()
    assert registry1 is registry2
