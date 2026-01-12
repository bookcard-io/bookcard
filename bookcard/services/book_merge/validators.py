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

"""Input validation for book merge operations."""

from bookcard.services.book_merge.exceptions import (
    DuplicateBookIdsError,
    InsufficientBooksError,
    InvalidKeepBookError,
)


class BookMergeValidator:
    """Validates merge operation inputs."""

    def validate_merge_request(self, book_ids: list[int], keep_book_id: int) -> None:
        """Validate merge request or raise ValidationError."""
        if len(book_ids) < 2:
            msg = "At least 2 books required for merge"
            raise InsufficientBooksError(msg)

        if len(set(book_ids)) != len(book_ids):
            msg = "Duplicate book IDs in merge request"
            raise DuplicateBookIdsError(msg)

        if keep_book_id not in book_ids:
            msg = "Keep book must be in the merge set"
            raise InvalidKeepBookError(msg)

    def validate_recommendation_request(self, book_ids: list[int]) -> None:
        """Validate recommendation request."""
        if len(book_ids) < 2:
            msg = "At least 2 books required for merge"
            raise InsufficientBooksError(msg)
