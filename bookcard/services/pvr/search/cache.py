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

"""Cache for search results."""

import threading

from bookcard.services.pvr.search.models import IndexerSearchResult


class SearchResultsCache:
    """Manages caching of search results."""

    def __init__(self) -> None:
        self._cache: dict[int, list[IndexerSearchResult]] = {}
        self._lock = threading.Lock()

    def store(self, tracked_book_id: int, results: list[IndexerSearchResult]) -> None:
        """Store search results in cache.

        Parameters
        ----------
        tracked_book_id : int
            Tracked book ID.
        results : list[IndexerSearchResult]
            List of search results.
        """
        with self._lock:
            self._cache[tracked_book_id] = results

    def get(self, tracked_book_id: int) -> list[IndexerSearchResult] | None:
        """Get search results from cache.

        Parameters
        ----------
        tracked_book_id : int
            Tracked book ID.

        Returns
        -------
        list[IndexerSearchResult] | None
            List of search results if found, None otherwise.
        """
        with self._lock:
            return self._cache.get(tracked_book_id)

    def clear(self, tracked_book_id: int) -> None:
        """Clear search results from cache.

        Parameters
        ----------
        tracked_book_id : int
            Tracked book ID.
        """
        with self._lock:
            self._cache.pop(tracked_book_id, None)
