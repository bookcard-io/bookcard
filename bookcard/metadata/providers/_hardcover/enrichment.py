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

"""Enrichment logic for merging search results with edition data."""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


class HardcoverEnrichment:
    """Handles enrichment of book data with detailed edition information."""

    @staticmethod
    def merge_book_with_editions(book_data: dict, edition_data: dict) -> dict:
        """Merge search result book data with detailed edition data.

        Parameters
        ----------
        book_data : dict
            Book data from search results.
        edition_data : dict
            Detailed book data with editions from edition query.

        Returns
        -------
        dict
            Merged book data with edition information.
        """
        merged = book_data.copy()

        # Use edition data for fields that are more complete there
        if edition_data.get("description") and not merged.get("description"):
            merged["description"] = edition_data["description"]

        # Merge series info from edition data if available
        HardcoverEnrichment._merge_series_info(merged, edition_data)

        # Merge tags from cached_tags if available
        HardcoverEnrichment._merge_tags_from_cached_tags(merged, edition_data)

        # Add editions data for identifier extraction
        editions = edition_data.get("editions", [])
        if editions:
            merged["editions"] = editions

        return merged

    @staticmethod
    def _merge_series_info(merged: dict, edition_data: dict) -> None:
        """Merge series information from edition data.

        Parameters
        ----------
        merged : dict
            Merged book data dictionary to update.
        edition_data : dict
            Edition data containing series information.
        """
        book_series = edition_data.get("book_series", [])
        if not (book_series and isinstance(book_series, list) and book_series[0]):
            return

        series_info = book_series[0]
        if not merged.get("series_names"):
            series = series_info.get("series", {})
            if series and series.get("name"):
                merged["series_names"] = [series["name"]]
        if merged.get("series_index") is None:
            position = series_info.get("position")
            if position is not None:
                merged["series_index"] = position

    @staticmethod
    def _merge_tags_from_cached_tags(merged: dict, edition_data: dict) -> None:
        """Merge tags from cached_tags in edition data.

        Parameters
        ----------
        merged : dict
            Merged book data dictionary to update.
        edition_data : dict
            Edition data containing cached_tags.
        """
        cached_tags = edition_data.get("cached_tags", [])
        if not cached_tags:
            return

        parsed_tags = HardcoverEnrichment._parse_cached_tags(cached_tags)
        if not parsed_tags:
            return

        existing_tags = merged.get("tags", [])
        if not isinstance(existing_tags, list):
            existing_tags = []

        merged["tags"] = list(set(existing_tags + parsed_tags))

    @staticmethod
    def _parse_cached_tags(cached_tags: str | list) -> list[str]:
        """Parse cached_tags into a list of tag names.

        Parameters
        ----------
        cached_tags : str | list
            Cached tags which may be a JSON string or list.

        Returns
        -------
        list[str]
            List of tag names.
        """
        # Handle cached_tags which may be a JSON string or list
        if isinstance(cached_tags, str):
            try:
                cached_tags = json.loads(cached_tags)
            except json.JSONDecodeError:
                return [cached_tags] if cached_tags else []

        if not isinstance(cached_tags, list):
            return []

        # Extract tag names from dict format if needed
        tag_names = []
        for tag in cached_tags:
            if isinstance(tag, dict):
                tag_name = tag.get("tag") or tag.get("name")
                if tag_name:
                    tag_names.append(str(tag_name))
            elif isinstance(tag, str):
                tag_names.append(tag)

        return tag_names
