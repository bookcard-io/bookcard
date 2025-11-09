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

"""Registry for metadata providers.

This module provides a registry pattern for discovering and managing
metadata providers dynamically.
"""

from __future__ import annotations

import importlib
import inspect
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from fundamental.metadata.base import MetadataProvider

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


class MetadataProviderRegistry:
    """Registry for discovering and managing metadata providers.

    This registry automatically discovers metadata provider classes in the
    `fundamental.metadata.providers` package and allows registration of
    custom providers.

    Attributes
    ----------
    _providers : dict[str, type[MetadataProvider]]
        Dictionary mapping provider IDs to provider classes.
    """

    def __init__(self) -> None:
        """Initialize the registry and auto-discover providers."""
        self._providers: dict[str, type[MetadataProvider]] = {}
        self._discover_providers()

    def _discover_providers(self) -> None:
        """Auto-discover metadata providers in the providers package."""
        providers_package = "fundamental.metadata.providers"
        providers_path = Path(__file__).parent / "providers"

        if not providers_path.exists():
            logger.warning(
                "Providers directory not found: %s. "
                "No providers will be auto-discovered.",
                providers_path,
            )
            return

        for file_path in providers_path.glob("*.py"):
            if file_path.name == "__init__.py":
                continue

            module_name = file_path.stem
            try:
                module = importlib.import_module(f"{providers_package}.{module_name}")
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(obj, MetadataProvider)
                        and obj is not MetadataProvider
                        and not inspect.isabstract(obj)
                    ):
                        try:
                            # Instantiate to get source info
                            instance = obj()
                            source_info = instance.get_source_info()
                            self._providers[source_info.id] = obj
                            logger.info(
                                "Registered metadata provider: %s (%s)",
                                source_info.id,
                                source_info.name,
                            )
                        except (ValueError, TypeError, AttributeError) as e:
                            logger.warning(
                                "Failed to register provider %s from %s: %s",
                                name,
                                module_name,
                                e,
                            )
            except ImportError as e:
                logger.debug("Could not import provider module %s: %s", module_name, e)
            except (ValueError, TypeError, AttributeError) as e:
                logger.warning("Error discovering provider %s: %s", module_name, e)

    def register(self, provider_class: type[MetadataProvider]) -> None:
        """Register a metadata provider class.

        Parameters
        ----------
        provider_class : type[MetadataProvider]
            Provider class to register.

        Raises
        ------
        ValueError
            If provider class is invalid or ID conflicts with existing provider.
        """
        if not issubclass(provider_class, MetadataProvider):
            msg = f"Provider class must subclass MetadataProvider: {provider_class}"
            raise TypeError(msg)

        try:
            instance = provider_class()
            source_info = instance.get_source_info()
            if source_info.id in self._providers:
                logger.warning(
                    "Provider %s already registered. Overwriting existing provider.",
                    source_info.id,
                )
            self._providers[source_info.id] = provider_class
            logger.info(
                "Registered metadata provider: %s (%s)",
                source_info.id,
                source_info.name,
            )
        except (ValueError, TypeError, AttributeError) as e:
            msg = f"Failed to register provider: {e}"
            raise ValueError(msg) from e

    def get_provider(self, provider_id: str) -> MetadataProvider | None:
        """Get a provider instance by ID.

        Parameters
        ----------
        provider_id : str
            Provider identifier.

        Returns
        -------
        MetadataProvider | None
            Provider instance if found, None otherwise.
        """
        provider_class = self._providers.get(provider_id)
        if provider_class is None:
            return None
        return provider_class()

    def get_all_providers(self) -> Iterator[MetadataProvider]:
        """Get all registered provider instances.

        Yields
        ------
        MetadataProvider
            Provider instance.
        """
        for provider_class in self._providers.values():
            yield provider_class()

    def get_enabled_providers(self) -> Iterator[MetadataProvider]:
        """Get all enabled provider instances.

        Yields
        ------
        MetadataProvider
            Enabled provider instance.
        """
        for provider in self.get_all_providers():
            if provider.is_enabled():
                yield provider

    def list_providers(self) -> list[str]:
        """List all registered provider IDs.

        Returns
        -------
        list[str]
            List of provider IDs.
        """
        return list(self._providers.keys())


# Global registry instance
_registry: MetadataProviderRegistry | None = None


def get_registry() -> MetadataProviderRegistry:
    """Get the global metadata provider registry.

    Returns
    -------
    MetadataProviderRegistry
        Global registry instance.
    """
    global _registry
    if _registry is None:
        _registry = MetadataProviderRegistry()
    return _registry
