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

"""Indexer registry for PVR system.

This module manages the registration of indexer implementations,
following SRP by separating registry concerns from factory logic.
"""

import logging

from bookcard.models.pvr import IndexerType
from bookcard.pvr.base import BaseIndexer

logger = logging.getLogger(__name__)

# Registry of indexer type to class mapping
_indexer_registry: dict[IndexerType, type[BaseIndexer]] = {}


def register_indexer(
    indexer_type: IndexerType, indexer_class: type[BaseIndexer]
) -> None:
    """Register an indexer implementation class.

    Parameters
    ----------
    indexer_type : IndexerType
        Type of indexer (Torznab, Newznab, etc.).
    indexer_class : type[BaseIndexer]
        Indexer class to register.

    Raises
    ------
    TypeError
        If indexer_class is not a subclass of BaseIndexer.
    """
    if not issubclass(indexer_class, BaseIndexer):
        msg = f"Indexer class must subclass BaseIndexer: {indexer_class}"
        raise TypeError(msg)

    _indexer_registry[indexer_type] = indexer_class
    logger.info(
        "Registered indexer type: %s -> %s", indexer_type, indexer_class.__name__
    )


def get_registered_indexer_types() -> list[IndexerType]:
    """Get list of registered indexer types.

    Returns
    -------
    list[IndexerType]
        List of registered indexer types.
    """
    return list(_indexer_registry.keys())


def get_indexer_class(indexer_type: IndexerType) -> type[BaseIndexer] | None:
    """Get registered indexer class for type.

    Parameters
    ----------
    indexer_type : IndexerType
        Indexer type.

    Returns
    -------
    type[BaseIndexer] | None
        Registered indexer class or None if not registered.
    """
    return _indexer_registry.get(indexer_type)
