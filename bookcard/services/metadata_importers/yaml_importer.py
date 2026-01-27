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

"""YAML format importer for book metadata."""

from __future__ import annotations

import contextlib
from datetime import UTC, date, datetime

from bookcard.api.schemas.books import BookUpdate
from bookcard.services.metadata_importers.base import MetadataImporter

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


class YamlImporter(MetadataImporter):
    """Importer for YAML format metadata.

    Follows SRP by focusing solely on YAML format import.
    """

    def can_handle(self, format_type: str) -> bool:
        """Check if this importer can handle YAML format.

        Parameters
        ----------
        format_type : str
            Format type identifier.

        Returns
        -------
        bool
            True if format is 'yaml' or 'yml'.
        """
        return format_type.lower() in ("yaml", "yml")

    def import_metadata(self, content: str) -> BookUpdate:
        """Import metadata from YAML content.

        Parameters
        ----------
        content : str
            YAML file content as string.

        Returns
        -------
        BookUpdate
            Book update object ready for form application.

        Raises
        ------
        ValueError
            If PyYAML is not installed or YAML parsing fails.
        """
        if yaml is None:
            msg = "YAML import requires PyYAML. Install with: pip install pyyaml"
            raise ValueError(msg)

        try:
            metadata_dict = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            msg = f"Invalid YAML format: {exc}"
            raise ValueError(msg) from exc

        if not isinstance(metadata_dict, dict):
            msg = "YAML content must be a dictionary"
            raise TypeError(msg)

        return YamlImporter._convert_to_book_update(metadata_dict)

    @staticmethod
    def _convert_to_book_update(metadata: dict) -> BookUpdate:
        """Convert parsed YAML metadata to BookUpdate format.

        Parameters
        ----------
        metadata : dict
            Parsed metadata dictionary.

        Returns
        -------
        BookUpdate
            Book update object.
        """
        update: dict = {}

        YamlImporter._extract_simple_fields(metadata, update)
        YamlImporter._extract_list_fields(metadata, update)
        YamlImporter._extract_identifiers(metadata, update)
        YamlImporter._extract_numeric_fields(metadata, update)

        return BookUpdate(**update)

    @staticmethod
    def _extract_simple_fields(metadata: dict, update: dict) -> None:
        """Extract simple string fields from metadata.

        Parameters
        ----------
        metadata : dict
            Parsed metadata dictionary.
        update : dict
            Dictionary to update with extracted fields.
        """
        if title := metadata.get("title"):
            update["title"] = str(title)

        if series := metadata.get("series"):
            update["series_name"] = str(series)

        if description := metadata.get("description"):
            update["description"] = str(description)

        if publisher := metadata.get("publisher"):
            update["publisher_name"] = str(publisher)

        if pubdate := metadata.get("pubdate"):
            update["pubdate"] = YamlImporter._parse_date(pubdate)

    @staticmethod
    def _extract_list_fields(metadata: dict, update: dict) -> None:
        """Extract list fields from metadata.

        Parameters
        ----------
        metadata : dict
            Parsed metadata dictionary.
        update : dict
            Dictionary to update with extracted fields.
        """
        authors = metadata.get("authors")
        if authors and isinstance(authors, list):
            update["author_names"] = [str(a) for a in authors]

        languages = metadata.get("languages")
        if languages and isinstance(languages, list):
            update["language_codes"] = [str(lang) for lang in languages]

        tags = metadata.get("tags")
        if tags and isinstance(tags, list):
            update["tag_names"] = [str(tag) for tag in tags]

    @staticmethod
    def _extract_identifiers(metadata: dict, update: dict) -> None:
        """Extract identifiers from metadata.

        Parameters
        ----------
        metadata : dict
            Parsed metadata dictionary.
        update : dict
            Dictionary to update with extracted fields.
        """
        identifiers = metadata.get("identifiers")
        if identifiers:
            if isinstance(identifiers, list):
                update["identifiers"] = YamlImporter._convert_identifier_list(
                    identifiers
                )
            elif isinstance(identifiers, dict):
                update["identifiers"] = YamlImporter._convert_identifier_dict(
                    identifiers
                )

        # Handle ISBN separately if present
        if isbn := metadata.get("isbn"):
            if not update.get("identifiers"):
                update["identifiers"] = []
            # Check if ISBN already in identifiers
            if not any(
                id_item.get("type", "").lower() == "isbn"
                for id_item in update["identifiers"]
            ):
                update["identifiers"].append({"type": "isbn", "val": str(isbn)})

    @staticmethod
    def _convert_identifier_list(identifiers: list) -> list[dict[str, str]]:
        """Convert identifier list to BookUpdate format.

        Parameters
        ----------
        identifiers : list
            List of identifier dictionaries.

        Returns
        -------
        list[dict[str, str]]
            Converted identifier list.
        """
        return [
            {
                "type": str(id_item.get("type", "")),
                "val": str(id_item.get("val", "")),
            }
            for id_item in identifiers
            if isinstance(id_item, dict)
        ]

    @staticmethod
    def _convert_identifier_dict(identifiers: dict) -> list[dict[str, str]]:
        """Convert identifier dict to BookUpdate format.

        Parameters
        ----------
        identifiers : dict
            Dictionary mapping type to value.

        Returns
        -------
        list[dict[str, str]]
            Converted identifier list.
        """
        return [{"type": str(k), "val": str(v)} for k, v in identifiers.items()]

    @staticmethod
    def _extract_numeric_fields(metadata: dict, update: dict) -> None:
        """Extract numeric fields from metadata.

        Parameters
        ----------
        metadata : dict
            Parsed metadata dictionary.
        update : dict
            Dictionary to update with extracted fields.
        """
        if series_index := metadata.get("series_index"):
            with contextlib.suppress(ValueError, TypeError):
                update["series_index"] = float(series_index)

        if rating := metadata.get("rating"):
            with contextlib.suppress(ValueError, TypeError):
                rating_value = int(rating)
                update["rating_value"] = max(0, min(5, rating_value))

    @staticmethod
    def _parse_date(date_value: str | datetime | None) -> datetime | None:
        """Parse date value to datetime.

        Parameters
        ----------
        date_value : str | datetime | None
            Date value to parse.

        Returns
        -------
        datetime | None
            Parsed datetime or None if invalid.
        """
        if date_value is None:
            return None

        if isinstance(date_value, datetime):
            return YamlImporter._normalize_datetime_timezone(date_value)

        # Handle date objects (from PyYAML)
        if isinstance(date_value, date):
            return datetime.combine(date_value, datetime.min.time()).replace(tzinfo=UTC)

        if not isinstance(date_value, str):
            return None

        # Try ISO format first
        dt = YamlImporter._parse_iso_date(date_value)
        if dt is not None:
            return dt

        # Try common date formats
        return YamlImporter._parse_date_formats(date_value)

    @staticmethod
    def _normalize_datetime_timezone(dt: datetime) -> datetime:
        """Normalize datetime to UTC if naive.

        Parameters
        ----------
        dt : datetime
            Datetime to normalize.

        Returns
        -------
        datetime
            Timezone-aware datetime.
        """
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt

    @staticmethod
    def _parse_iso_date(date_str: str) -> datetime | None:
        """Parse ISO format date string.

        Parameters
        ----------
        date_str : str
            ISO format date string.

        Returns
        -------
        datetime | None
            Parsed datetime or None if invalid.
        """
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return YamlImporter._normalize_datetime_timezone(dt)
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _parse_date_formats(date_str: str) -> datetime | None:
        """Parse date string using common formats.

        Parameters
        ----------
        date_str : str
            Date string to parse.

        Returns
        -------
        datetime | None
            Parsed datetime or None if invalid.
        """
        date_formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
        ]

        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)  # noqa: DTZ007
                return YamlImporter._normalize_datetime_timezone(dt)
            except ValueError:
                continue

        return None
