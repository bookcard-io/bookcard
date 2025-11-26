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

"""Parser for Hardcover API responses."""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


class HardcoverResponseParser:
    """Parses raw API responses into intermediate structures.

    This class handles the parsing of GraphQL responses, extracting
    book documents from various response formats.
    """

    @staticmethod
    def parse_search_results(
        results_data: dict | list | str | None,
    ) -> list[dict]:
        """Parse search results from API response.

        Parameters
        ----------
        results_data : dict | list | str | None
            Raw results data from API.

        Returns
        -------
        list[dict]
            List of book documents.
        """
        if results_data is None:
            return []

        # Handle case where results might be a JSON string
        if isinstance(results_data, str):
            try:
                results_data = json.loads(results_data)
            except json.JSONDecodeError as e:
                logger.warning(
                    "Hardcover search results is a string but not valid JSON: %s", e
                )
                return []

        # Extract books from results structure: results.hits[].document
        if isinstance(results_data, dict):
            hits = results_data.get("hits", [])
            if not isinstance(hits, list):
                logger.warning(
                    "Hardcover search hits is not a list, got %s", type(hits)
                )
                return []
            # Extract document from each hit
            return [
                hit.get("document")
                for hit in hits
                if isinstance(hit, dict) and hit.get("document")
            ]

        if isinstance(results_data, list):
            # Direct list of books (fallback for different response format)
            return results_data

        logger.warning(
            "Hardcover search results has unexpected type: %s",
            type(results_data),
        )
        return []

    @staticmethod
    def extract_search_data(data: dict) -> dict | list | str | None:
        """Extract search results from GraphQL response.

        Parameters
        ----------
        data : dict
            Full GraphQL response data.

        Returns
        -------
        dict | list | str | None
            Raw results data.
        """
        search_data = data.get("data", {}).get("search", {})
        return search_data.get("results")

    @staticmethod
    def extract_edition_data(data: dict) -> dict | None:
        """Extract edition data from GraphQL response.

        Parameters
        ----------
        data : dict
            Full GraphQL response data.

        Returns
        -------
        dict | None
            Book data with editions, or None if not found.
        """
        books = data.get("data", {}).get("books", [])
        if books and isinstance(books, list) and books[0]:
            return books[0]
        return None
