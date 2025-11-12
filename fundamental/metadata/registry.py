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

    def get_enabled_providers(
        self, enable_providers: list[str] | None = None
    ) -> Iterator[MetadataProvider]:
        """Get enabled provider instances.

        Parameters
        ----------
        enable_providers : list[str] | None
            List of provider names to enable. If None or empty, all available
            providers are enabled. Unknown provider names are ignored.

        Yields
        ------
        MetadataProvider
            Enabled provider instance.
        """
        all_providers = list(self.get_all_providers())

        # If enable_providers is None or empty, return all providers that are enabled
        if not enable_providers:
            for provider in all_providers:
                if provider.is_enabled():
                    yield provider
            return

        # Filter by provider names
        # Get all available provider names for matching
        available_names = {
            provider.get_source_info().name for provider in all_providers
        }

        # Filter to only include providers whose names are in enable_providers
        # and that are also enabled by their is_enabled() method
        enabled_names_set = set(enable_providers)
        matching_names = enabled_names_set & available_names

        # Yield providers that match the enabled names and are also enabled
        for provider in all_providers:
            provider_name = provider.get_source_info().name
            if provider_name in matching_names and provider.is_enabled():
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
