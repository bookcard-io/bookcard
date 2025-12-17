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

"""Maps Hardcover book data to MetadataRecord."""

from __future__ import annotations

import logging

from bookcard.metadata.providers._hardcover.extractors import (
    AuthorsExtractor,
    CoverExtractor,
    IdentifiersExtractor,
    LanguagesExtractor,
    PublishedDateExtractor,
    PublisherExtractor,
    SeriesExtractor,
    TagsExtractor,
)
from bookcard.metadata.providers._hardcover.utils import PARSE_EXCEPTIONS
from bookcard.models.metadata import MetadataRecord

logger = logging.getLogger(__name__)


class HardcoverBookMapper:
    """Maps Hardcover book data dictionaries to MetadataRecord objects.

    This class uses a registry of extractors to extract fields from
    book data, making it easy to extend with new extractors.
    """

    BOOK_URL_BASE = "https://hardcover.app/book/"
    SOURCE_ID = "hardcover"

    def __init__(self) -> None:
        """Initialize mapper with default extractors."""
        self._extractors = {
            "authors": AuthorsExtractor(),
            "cover_url": CoverExtractor(),
            "identifiers": IdentifiersExtractor(),
            "series": SeriesExtractor(),
            "publisher": PublisherExtractor(),
            "published_date": PublishedDateExtractor(),
            "tags": TagsExtractor(),
            "languages": LanguagesExtractor(),
        }

    def map_to_record(self, book_data: dict) -> MetadataRecord | None:
        """Map book data dictionary to MetadataRecord.

        Parameters
        ----------
        book_data : dict
            Book data from API response.

        Returns
        -------
        MetadataRecord | None
            Parsed metadata record, or None if parsing fails.
        """
        try:
            # Extract basic info
            book_id = book_data.get("id")
            if not book_id:
                return None

            title = book_data.get("title", "")
            if not title:
                return None

            # Extract fields using extractors
            authors_result = self._extractors["authors"].extract(book_data)
            authors = authors_result if isinstance(authors_result, list) else []
            description = book_data.get("description")
            cover_url_result = self._extractors["cover_url"].extract(book_data)
            cover_url = cover_url_result if isinstance(cover_url_result, str) else None
            identifiers_result = self._extractors["identifiers"].extract(book_data)
            identifiers = (
                identifiers_result if isinstance(identifiers_result, dict) else {}
            )
            series_result = self._extractors["series"].extract(book_data)
            if isinstance(series_result, tuple) and len(series_result) == 2:
                series, series_index = series_result
            else:
                series, series_index = None, None
            publisher_result = self._extractors["publisher"].extract(book_data)
            publisher = publisher_result if isinstance(publisher_result, str) else None
            published_date_result = self._extractors["published_date"].extract(
                book_data
            )
            published_date = (
                published_date_result
                if isinstance(published_date_result, str)
                else None
            )
            tags_result = self._extractors["tags"].extract(book_data)
            tags = tags_result if isinstance(tags_result, list) else []
            languages_result = self._extractors["languages"].extract(book_data)
            languages = languages_result if isinstance(languages_result, list) else []

            # Extract rating
            rating = book_data.get("rating")
            if rating is not None:
                try:
                    rating = float(rating)
                except (ValueError, TypeError):
                    rating = None

            # Build URL
            slug = book_data.get("slug")
            if slug:
                url = f"{self.BOOK_URL_BASE}{slug}"
            else:
                url = f"{self.BOOK_URL_BASE}{book_id}"

            # Build record
            return MetadataRecord(
                source_id=self.SOURCE_ID,
                external_id=str(book_id),
                title=title,
                authors=authors,
                url=url,
                cover_url=cover_url,
                description=description,
                series=series,
                series_index=series_index,
                identifiers=identifiers,
                publisher=publisher,
                published_date=published_date,
                rating=rating,
                languages=languages,
                tags=tags,
            )

        except PARSE_EXCEPTIONS as e:
            logger.warning("Error parsing Hardcover book: %s", e)
            return None
