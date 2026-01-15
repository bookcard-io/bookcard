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

"""Validators for Anna's Archive search parameters."""

import logging
from typing import Final

logger = logging.getLogger(__name__)


class SearchValidator:
    """Validates search parameters."""

    MAX_RESULTS_LIMIT: Final[int] = 1000
    MIN_RESULTS: Final[int] = 1
    MAX_QUERY_LENGTH: Final[int] = 500

    @classmethod
    def validate_max_results(cls, max_results: int) -> int:
        """Validate and normalize max_results."""
        if max_results < cls.MIN_RESULTS:
            msg = f"max_results must be at least {cls.MIN_RESULTS}, got {max_results}"
            raise ValueError(msg)

        if max_results > cls.MAX_RESULTS_LIMIT:
            logger.warning(
                "max_results %d exceeds limit %d, capping to limit",
                max_results,
                cls.MAX_RESULTS_LIMIT,
            )
            return cls.MAX_RESULTS_LIMIT

        return max_results

    @classmethod
    def validate_query_length(cls, query: str) -> None:
        """Validate query length."""
        if len(query) > cls.MAX_QUERY_LENGTH:
            msg = f"Query exceeds maximum length of {cls.MAX_QUERY_LENGTH} characters"
            raise ValueError(msg)

    @classmethod
    def validate_isbn(cls, isbn: str) -> str:
        """Validate and normalize ISBN."""
        # Remove common separators
        normalized = isbn.replace("-", "").replace(" ", "")

        # Check length (ISBN-10 or ISBN-13)
        if len(normalized) not in (10, 13):
            msg = f"Invalid ISBN length: {len(normalized)}"
            raise ValueError(msg)

        if not normalized.isdigit():
            msg = "ISBN must contain only digits"
            raise ValueError(msg)

        return normalized
