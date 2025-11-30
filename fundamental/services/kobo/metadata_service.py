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

"""Kobo metadata service.

Formats book metadata, entitlements, and reading states in Kobo API format.
Handles KEPUB format detection and conversion.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fundamental.models.reading import ReadStatusEnum
from fundamental.repositories.models import BookWithFullRelations, BookWithRelations

if TYPE_CHECKING:
    from fundamental.models.core import Book
    from fundamental.models.kobo import KoboReadingState
    from fundamental.models.reading import ReadStatus


# Kobo-supported formats mapping
KOBO_FORMATS: dict[str, list[str]] = {
    "KEPUB": ["KEPUB"],
    "EPUB": ["EPUB3", "EPUB"],
}


def convert_to_kobo_timestamp_string(dt: datetime | None) -> str:
    """Convert datetime to Kobo timestamp string format.

    Parameters
    ----------
    dt : datetime | None
        Datetime to convert.

    Returns
    -------
    str
        Timestamp string in format "YYYY-MM-DDTHH:MM:SSZ".
    """
    if dt is None:
        dt = datetime.now(UTC)
    dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class KoboMetadataService:
    """Service for formatting book metadata in Kobo API format.

    Handles conversion of book data, entitlements, and reading states
    to the format expected by Kobo devices.

    Parameters
    ----------
    base_url : str
        Base URL for constructing download URLs.
    auth_token : str
        Authentication token for download URLs.
    """

    def __init__(self, base_url: str, auth_token: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._auth_token = auth_token

    def get_download_url(self, book_id: int, book_format: str) -> str:
        """Get download URL for a book format.

        Parameters
        ----------
        book_id : int
            Book ID.
        book_format : str
            Book format (e.g., "EPUB", "KEPUB").

        Returns
        -------
        str
            Download URL.
        """
        return f"{self._base_url}/kobo/{self._auth_token}/download/{book_id}/{book_format.lower()}"

    def create_book_entitlement(
        self, book: Book, archived: bool = False
    ) -> dict[str, object]:
        """Create book entitlement in Kobo format.

        Parameters
        ----------
        book : Book
            Book instance.
        archived : bool
            Whether the book is archived.

        Returns
        -------
        dict[str, object]
            Book entitlement dictionary.
        """
        book_uuid = str(book.uuid) if book.uuid else str(uuid.uuid4())
        timestamp = book.timestamp or datetime.now(UTC)
        last_modified = book.last_modified or datetime.now(UTC)

        return {
            "Accessibility": "Full",
            "ActivePeriod": {
                "From": convert_to_kobo_timestamp_string(datetime.now(UTC))
            },
            "Created": convert_to_kobo_timestamp_string(timestamp),
            "CrossRevisionId": book_uuid,
            "Id": book_uuid,
            "IsRemoved": archived,
            "IsHiddenFromArchive": False,
            "IsLocked": False,
            "LastModified": convert_to_kobo_timestamp_string(last_modified),
            "OriginCategory": "Imported",
            "RevisionId": book_uuid,
            "Status": "Active",
        }

    def get_book_metadata(
        self, book_with_rels: BookWithRelations | BookWithFullRelations
    ) -> dict[str, object]:
        """Get book metadata in Kobo format.

        Parameters
        ----------
        book_with_rels : BookWithRelations | BookWithFullRelations
            Book with relations.

        Returns
        -------
        dict[str, object]
            Book metadata dictionary.
        """
        book = book_with_rels.book
        book_uuid = str(book.uuid) if book.uuid else str(uuid.uuid4())

        # Get download URLs for supported formats
        download_urls = []
        formats = getattr(book_with_rels, "formats", []) or []

        # Prefer KEPUB if available
        kepub_formats = [f for f in formats if f.get("format", "").upper() == "KEPUB"]
        formats_to_process = kepub_formats if kepub_formats else formats

        for format_data in formats_to_process:
            format_name = format_data.get("format", "").upper()
            if format_name not in KOBO_FORMATS:
                continue

            for kobo_format in KOBO_FORMATS[format_name]:
                # Check if pre-paginated EPUB (EPUB3FL)
                # Can be enhanced later with EPUB layout detection

                size = format_data.get("size", 0)
                download_urls.append({
                    "Format": kobo_format,
                    "Size": size,
                    "Url": self.get_download_url(book.id or 0, format_name),
                    "Platform": "Generic",
                })

        # Get authors
        authors = book_with_rels.authors or []
        contributor_roles = [{"Name": author} for author in authors]
        contributors = authors if authors else None

        # Get description
        description = None
        if isinstance(book_with_rels, BookWithFullRelations):
            description = book_with_rels.description

        # Get publisher
        publisher = None
        if isinstance(book_with_rels, BookWithFullRelations):
            publisher = book_with_rels.publisher

        # Get language (default to 'en')
        language = "en"
        if isinstance(book_with_rels, BookWithFullRelations):
            languages = book_with_rels.languages
            if languages:
                # Use first language, convert ISO 639-3 to ISO 639-1 if needed
                lang_code = languages[0]
                # Simple mapping for common languages
                lang_map: dict[str, str] = {
                    "eng": "en",
                    "fra": "fr",
                    "spa": "es",
                    "deu": "de",
                    "ita": "it",
                    "por": "pt",
                    "jpn": "ja",
                    "zho": "zh",
                    "rus": "ru",
                }
                language = lang_map.get(
                    lang_code.lower(), lang_code[:2] if len(lang_code) >= 2 else "en"
                )

        # Build metadata
        metadata: dict[str, object] = {
            "Categories": ["00000000-0000-0000-0000-000000000001"],
            "CoverImageId": book_uuid,
            "CrossRevisionId": book_uuid,
            "CurrentDisplayPrice": {"CurrencyCode": "USD", "TotalAmount": 0},
            "CurrentLoveDisplayPrice": {"TotalAmount": 0},
            "Description": description,
            "DownloadUrls": download_urls,
            "EntitlementId": book_uuid,
            "ExternalIds": [],
            "Genre": "00000000-0000-0000-0000-000000000001",
            "IsEligibleForKoboLove": False,
            "IsInternetArchive": False,
            "IsPreOrder": False,
            "IsSocialEnabled": True,
            "Language": language,
            "PhoneticPronunciations": {},
            "PublicationDate": convert_to_kobo_timestamp_string(book.pubdate),
            "Publisher": {"Imprint": "", "Name": publisher},
            "RevisionId": book_uuid,
            "Title": book.title,
            "WorkId": book_uuid,
            "ContributorRoles": contributor_roles,
            "Contributors": contributors,
        }

        # Add series if available
        if book_with_rels.series:
            series_name = book_with_rels.series
            series_index = book.series_index if book.series_index is not None else 1.0
            series_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, series_name))
            metadata["Series"] = {
                "Name": series_name,
                "Number": int(series_index)
                if isinstance(series_index, (int, float))
                else 1,
                "NumberFloat": float(series_index)
                if isinstance(series_index, (int, float))
                else 1.0,
                "Id": series_id,
            }

        return metadata

    def get_reading_state_response(
        self,
        book: Book,
        reading_state: KoboReadingState,
        read_status: ReadStatus | None = None,
    ) -> dict[str, object]:
        """Get reading state response in Kobo format.

        Parameters
        ----------
        book : Book
            Book instance.
        reading_state : KoboReadingState
            Kobo reading state.
        read_status : ReadStatus | None
            Optional read status for status info.

        Returns
        -------
        dict[str, object]
            Reading state response dictionary.
        """
        book_uuid = str(book.uuid) if book.uuid else str(uuid.uuid4())
        timestamp = book.timestamp or datetime.now(UTC)

        response: dict[str, object] = {
            "EntitlementId": book_uuid,
            "Created": convert_to_kobo_timestamp_string(timestamp),
            "LastModified": convert_to_kobo_timestamp_string(
                reading_state.last_modified
            ),
            "PriorityTimestamp": convert_to_kobo_timestamp_string(
                reading_state.priority_timestamp
            ),
        }

        # Add status info
        if read_status:
            status_str = self._get_read_status_for_kobo(read_status.status)
            status_info: dict[str, object] = {
                "LastModified": convert_to_kobo_timestamp_string(
                    read_status.updated_at
                ),
                "Status": status_str,
                "TimesStartedReading": 1,  # Can be enhanced with actual tracking
            }
            if read_status.first_opened_at:
                status_info["LastTimeStartedReading"] = (
                    convert_to_kobo_timestamp_string(read_status.first_opened_at)
                )
            response["StatusInfo"] = status_info
        else:
            response["StatusInfo"] = {
                "LastModified": convert_to_kobo_timestamp_string(
                    reading_state.last_modified
                ),
                "Status": "ReadyToRead",
                "TimesStartedReading": 0,
            }

        # Add statistics
        if reading_state.statistics:
            stats: dict[str, object] = {
                "LastModified": convert_to_kobo_timestamp_string(
                    reading_state.statistics.last_modified
                ),
            }
            if reading_state.statistics.spent_reading_minutes:
                stats["SpentReadingMinutes"] = (
                    reading_state.statistics.spent_reading_minutes
                )
            if reading_state.statistics.remaining_time_minutes:
                stats["RemainingTimeMinutes"] = (
                    reading_state.statistics.remaining_time_minutes
                )
            response["Statistics"] = stats
        else:
            response["Statistics"] = {
                "LastModified": convert_to_kobo_timestamp_string(
                    reading_state.last_modified
                ),
            }

        # Add bookmark
        if reading_state.current_bookmark:
            bookmark: dict[str, object] = {
                "LastModified": convert_to_kobo_timestamp_string(
                    reading_state.current_bookmark.last_modified
                ),
            }
            if reading_state.current_bookmark.progress_percent is not None:
                bookmark["ProgressPercent"] = (
                    reading_state.current_bookmark.progress_percent
                )
            if (
                reading_state.current_bookmark.content_source_progress_percent
                is not None
            ):
                bookmark["ContentSourceProgressPercent"] = (
                    reading_state.current_bookmark.content_source_progress_percent
                )
            if reading_state.current_bookmark.location_value:
                bookmark["Location"] = {
                    "Value": reading_state.current_bookmark.location_value,
                    "Type": reading_state.current_bookmark.location_type or "",
                    "Source": reading_state.current_bookmark.location_source or "",
                }
            response["CurrentBookmark"] = bookmark
        else:
            response["CurrentBookmark"] = {
                "LastModified": convert_to_kobo_timestamp_string(
                    reading_state.last_modified
                ),
            }

        return response

    def _get_read_status_for_kobo(self, status: ReadStatusEnum | None) -> str:
        """Convert read status to Kobo format.

        Parameters
        ----------
        status : ReadStatusEnum | None
            Read status.

        Returns
        -------
        str
            Kobo status string.
        """
        status_map: dict[ReadStatusEnum | None, str] = {
            None: "ReadyToRead",
            ReadStatusEnum.NOT_READ: "ReadyToRead",
            ReadStatusEnum.READ: "Finished",
            ReadStatusEnum.READING: "Reading",
        }
        return status_map.get(status, "ReadyToRead")

    def get_kepub_format(
        self, book_with_rels: BookWithRelations | BookWithFullRelations
    ) -> str | None:
        """Check if book has KEPUB format.

        Parameters
        ----------
        book_with_rels : BookWithRelations | BookWithFullRelations
            Book with relations.

        Returns
        -------
        str | None
            "KEPUB" if available, None otherwise.
        """
        formats = getattr(book_with_rels, "formats", []) or []
        for format_data in formats:
            if format_data.get("format", "").upper() == "KEPUB":
                return "KEPUB"
        return None
