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

"""Scoring logic for book merge recommendation."""

from bookcard.models.core import Book
from bookcard.models.media import Data
from bookcard.services.book_merge.config import ScoringConfig


class BookScorer:
    """Calculates scores for books to determine the best merge candidate."""

    def __init__(self, config: ScoringConfig) -> None:
        self._config = config

    def score_book(self, book: Book, data_records: list[Data]) -> int:
        """Score a book based on its completeness and quality."""
        score = 0
        if book.has_cover:
            score += self._config.cover_weight

        score += len(data_records) * self._config.file_count_weight

        for d in data_records:
            score += self._config.format_weights.get(d.format.upper(), 0)

        # Metadata completeness
        if book.pubdate:
            score += self._config.metadata_field_weight
        # Check publisher link via relationship if available, or direct attribute if mapped
        if hasattr(book, "publisher") and book.publisher:
            score += self._config.metadata_field_weight
        if book.isbn:
            score += self._config.metadata_field_weight
        if book.lccn:
            score += self._config.metadata_field_weight

        return score
