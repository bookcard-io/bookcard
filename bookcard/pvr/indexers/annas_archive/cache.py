# Copyright (C) 2026 knguyen and others
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

"""Cache implementation for Anna's Archive indexer."""

import hashlib
import json
import time

from bookcard.pvr.models import ReleaseInfo


class SearchCache:
    """Cache for search results."""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300) -> None:
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[float, list[ReleaseInfo]]] = {}

    def get(self, cache_key: str) -> list[ReleaseInfo] | None:
        """Get cached results if not expired."""
        if cache_key not in self._cache:
            return None

        timestamp, results = self._cache[cache_key]

        # Check if expired
        if time.time() - timestamp > self._ttl_seconds:
            del self._cache[cache_key]
            return None

        return results

    def set(self, cache_key: str, results: list[ReleaseInfo]) -> None:
        """Cache results with timestamp."""
        # Implement simple LRU by removing oldest if at capacity
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache.items(), key=lambda x: x[1][0])[0]
            del self._cache[oldest_key]

        self._cache[cache_key] = (time.time(), results)

    @staticmethod
    def make_cache_key(
        query: str,
        title: str | None,
        author: str | None,
        isbn: str | None,
        max_results: int,
        page: int,
    ) -> str:
        """Create cache key from search parameters."""
        params = {
            "query": query,
            "title": title,
            "author": author,
            "isbn": isbn,
            "max_results": max_results,
            "page": page,
        }
        # Create stable hash of parameters
        params_json = json.dumps(params, sort_keys=True)
        return hashlib.sha256(params_json.encode()).hexdigest()
