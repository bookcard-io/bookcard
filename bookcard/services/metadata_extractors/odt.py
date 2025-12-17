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

"""Metadata extraction strategy for ODT (OpenDocument Text) files.

ODT files are ZIP archives containing XML files with metadata.
Extracts metadata from the meta.xml file using OpenDocument format.
"""

from __future__ import annotations

import zipfile
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from lxml import etree  # type: ignore[attr-defined]

from bookcard.services.book_metadata import BookMetadata
from bookcard.services.metadata_extractors.base import MetadataExtractionStrategy

if TYPE_CHECKING:
    from pathlib import Path

# OpenDocument namespaces
NS_OFFICE = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_META = "urn:oasis:names:tc:opendocument:xmlns:meta:1.0"


class OdtMetadataExtractor(MetadataExtractionStrategy):
    """Metadata extraction strategy for ODT files."""

    def can_handle(self, file_format: str) -> bool:
        """Check if format is ODT."""
        format_upper = file_format.upper().lstrip(".")
        return format_upper == "ODT"

    def extract(self, file_path: Path, original_filename: str) -> BookMetadata:
        """Extract metadata from ODT file.

        Parameters
        ----------
        file_path : Path
            Path to the ODT file.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        try:
            with zipfile.ZipFile(file_path, "r") as odt_zip:
                # Read meta.xml
                try:
                    meta_xml = odt_zip.read("meta.xml")
                    return self._parse_meta_xml(meta_xml, original_filename)
                except KeyError:
                    return self._extract_from_filename(original_filename)
        except (zipfile.BadZipFile, OSError):
            return self._extract_from_filename(original_filename)

    def _parse_meta_xml(
        self, xml_content: bytes, original_filename: str
    ) -> BookMetadata:
        """Parse meta.xml to extract metadata.

        Parameters
        ----------
        xml_content : bytes
            XML content from meta.xml.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        try:
            root = etree.fromstring(xml_content)
            ns = {
                "office": NS_OFFICE,
                "dc": NS_DC,
                "meta": NS_META,
            }

            # Extract title
            title_elem = root.find(".//dc:title", ns)
            title = (
                title_elem.text.strip()
                if title_elem is not None and title_elem.text
                else self._extract_title_from_filename(original_filename)
            )

            # Extract creator (author)
            creator_elem = root.find(".//dc:creator", ns)
            author = (
                creator_elem.text.strip()
                if creator_elem is not None and creator_elem.text
                else "Unknown"
            )

            # Extract subject (description)
            subject_elem = root.find(".//dc:subject", ns)
            description = (
                subject_elem.text.strip()
                if subject_elem is not None and subject_elem.text
                else ""
            )

            # Extract keywords (tags)
            keywords_elem = root.find(".//meta:keyword", ns)
            tags = None
            if keywords_elem is not None and keywords_elem.text:
                keywords = keywords_elem.text.strip()
                if keywords:
                    # Keywords might be comma or semicolon separated
                    tags = [kw.strip() for kw in keywords.split(",") if kw.strip()]

            # Extract publisher
            publisher = None
            # ODT doesn't have a standard publisher field

            # Extract creation date
            pubdate = None
            date_elem = root.find(".//meta:creation-date", ns)
            if date_elem is not None and date_elem.text:
                pubdate = self._parse_iso_date(date_elem.text)

            # Extract modification date
            modified = None
            date_elem = root.find(".//meta:date-string", ns)
            if date_elem is not None and date_elem.text:
                modified = self._parse_iso_date(date_elem.text)

            # Extract language
            language_elem = root.find(".//dc:language", ns)
            languages = None
            if language_elem is not None and language_elem.text:
                languages = [language_elem.text.strip()]

            return BookMetadata(
                title=title,
                author=author,
                description=description,
                tags=tags,
                publisher=publisher,
                pubdate=pubdate,
                modified=modified,
                languages=languages,
            )
        except (etree.XMLSyntaxError, ValueError, AttributeError):
            return self._extract_from_filename(original_filename)

    def _parse_iso_date(self, date_str: str) -> datetime | None:
        """Parse ISO 8601 date string.

        Parameters
        ----------
        date_str : str
            ISO 8601 date string.

        Returns
        -------
        datetime | None
            Parsed datetime or None.
        """
        if not date_str:
            return None

        # Try common ISO 8601 formats
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                if "Z" in fmt and date_str.endswith("Z"):
                    return datetime.strptime(date_str, fmt).replace(tzinfo=UTC)
                if "+" in date_str:
                    # Has timezone offset
                    date_str_clean = date_str.split("+")[0].split("-")[0]
                    return datetime.strptime(
                        date_str_clean, "%Y-%m-%dT%H:%M:%S"
                    ).replace(tzinfo=UTC)
                return datetime.strptime(date_str, fmt).replace(tzinfo=UTC)
            except (ValueError, TypeError):
                continue

        return None

    def _extract_from_filename(self, filename: str) -> BookMetadata:
        """Extract metadata from filename only.

        Parameters
        ----------
        filename : str
            Filename.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        title = self._extract_title_from_filename(filename)
        return BookMetadata(title=title, author="Unknown")

    @staticmethod
    def _extract_title_from_filename(filename: str) -> str:
        """Extract title from filename.

        Parameters
        ----------
        filename : str
            Filename.

        Returns
        -------
        str
            Title (filename without extension).
        """
        from pathlib import Path

        stem = Path(filename).stem
        return stem.strip() or filename
