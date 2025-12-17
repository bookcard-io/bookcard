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

"""Task metadata normalization service.

Handles normalization and merging of task metadata, ensuring consistency
across different sources (task_instance.metadata, task.task_data).
Follows SRP by focusing solely on metadata normalization concerns.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TaskMetadataNormalizer:
    """Service for normalizing and merging task metadata.

    Ensures metadata from different sources is properly merged and normalized.
    Follows SRP by handling only metadata normalization logic.
    """

    @staticmethod
    def normalize_metadata(
        task_instance_metadata: dict[str, Any] | None,
        task_data: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Normalize and merge metadata from task instance and task data.

        Ensures book_ids is present and properly formatted.

        Parameters
        ----------
        task_instance_metadata : dict[str, Any] | None
            Metadata from the task instance.
        task_data : dict[str, Any] | None
            Metadata from the task's task_data field.

        Returns
        -------
        dict[str, Any]
            Normalized and merged metadata dictionary.
        """
        final_metadata = dict(task_instance_metadata) if task_instance_metadata else {}

        # Normalize book_ids - ensure it's always an array
        book_ids = TaskMetadataNormalizer._extract_book_ids(
            final_metadata,
            task_data,
        )

        if book_ids:
            final_metadata["book_ids"] = book_ids

        return final_metadata

    @staticmethod
    def _extract_book_ids(
        task_instance_metadata: dict[str, Any],
        task_data: dict[str, Any] | None,
    ) -> list[int] | None:
        """Extract book_ids from metadata sources.

        Checks both task_instance_metadata and task_data for book_ids.

        Parameters
        ----------
        task_instance_metadata : dict[str, Any]
            Metadata from task instance.
        task_data : dict[str, Any] | None
            Metadata from task data.

        Returns
        -------
        list[int] | None
            List of book IDs, or None if not found.
        """
        # Check task_instance_metadata first (most up-to-date)
        book_ids = TaskMetadataNormalizer._try_get_book_ids_from_dict(
            task_instance_metadata,
        )
        if book_ids:
            return book_ids

        # Check task_data for book_ids
        if task_data:
            book_ids = TaskMetadataNormalizer._try_get_book_ids_from_dict(task_data)
            if book_ids:
                return book_ids

        return None

    @staticmethod
    def _try_get_book_ids_from_dict(metadata: dict[str, Any]) -> list[int] | None:
        """Try to extract book_ids from a metadata dictionary.

        Parameters
        ----------
        metadata : dict[str, Any]
            Metadata dictionary to check.

        Returns
        -------
        list[int] | None
            Normalized book_ids list, or None if not found/invalid.
        """
        if "book_ids" not in metadata:
            return None

        book_ids = metadata["book_ids"]
        if isinstance(book_ids, list) and len(book_ids) > 0:
            normalized = TaskMetadataNormalizer._normalize_book_ids_list(book_ids)
            if normalized:
                logger.debug("Found book_ids in metadata: %s", normalized)
                return normalized

        return None

    @staticmethod
    def _normalize_book_ids_list(book_ids: list[Any]) -> list[int] | None:
        """Normalize a list of book IDs to ensure all are integers.

        Parameters
        ----------
        book_ids : list[Any]
            List of book IDs (may contain mixed types).

        Returns
        -------
        list[int] | None
            Normalized list of integers, or None if invalid.
        """
        if not isinstance(book_ids, list) or len(book_ids) == 0:
            return None

        normalized: list[int] = []
        for item in book_ids:
            if isinstance(item, int):
                normalized.append(item)
            elif isinstance(item, str):
                try:
                    normalized.append(int(item))
                except (ValueError, TypeError):
                    continue

        return normalized if normalized else None
