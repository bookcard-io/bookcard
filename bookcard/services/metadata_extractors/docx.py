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

"""Metadata extraction strategy for DOCX (Microsoft Word) files.

DOCX files are ZIP archives containing XML files with metadata.
Extracts metadata from the core properties XML file (docProps/core.xml).
"""

from __future__ import annotations

import re
import zipfile
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from lxml import etree  # type: ignore[attr-defined]

from bookcard.services.book_metadata import BookMetadata
from bookcard.services.metadata_extractors.base import MetadataExtractionStrategy

if TYPE_CHECKING:
    from pathlib import Path

# Office Open XML namespaces
NS_CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_DCTERMS = "http://purl.org/dc/terms/"


class DocxMetadataExtractor(MetadataExtractionStrategy):
    """Metadata extraction strategy for DOCX files."""

    def can_handle(self, file_format: str) -> bool:
        """Check if format is DOCX."""
        format_upper = file_format.upper().lstrip(".")
        return format_upper == "DOCX"

    def extract(self, file_path: Path, original_filename: str) -> BookMetadata:
        """Extract metadata from DOCX file.

        Parameters
        ----------
        file_path : Path
            Path to the DOCX file.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        try:
            with zipfile.ZipFile(file_path, "r") as docx_zip:
                # Read core properties
                try:
                    core_props_xml = docx_zip.read("docProps/core.xml")
                    return self._parse_core_properties(
                        core_props_xml, original_filename
                    )
                except KeyError:
                    # No core.xml, try app.xml for title
                    try:
                        app_props_xml = docx_zip.read("docProps/app.xml")
                        return self._parse_app_properties(
                            app_props_xml, original_filename
                        )
                    except KeyError:
                        return self._extract_from_filename(original_filename)
        except (zipfile.BadZipFile, OSError):
            return self._extract_from_filename(original_filename)

    def _parse_core_properties(
        self, xml_content: bytes, original_filename: str
    ) -> BookMetadata:
        """Parse core properties XML.

        Parameters
        ----------
        xml_content : bytes
            XML content from docProps/core.xml.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        try:
            root = etree.fromstring(xml_content)
            ns = {"cp": NS_CP, "dc": NS_DC, "dcterms": NS_DCTERMS}

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
            keywords_elem = root.find(".//cp:keywords", ns)
            tags = None
            if keywords_elem is not None and keywords_elem.text:
                keywords = keywords_elem.text.strip()
                if keywords:
                    # Keywords might be comma or semicolon separated
                    tags = [
                        kw.strip() for kw in re.split(r"[,;]", keywords) if kw.strip()
                    ]

            # Extract publisher
            publisher = None
            # DOCX doesn't have a standard publisher field in core properties
            # But we can check for it in custom properties if needed

            # Extract publication date
            pubdate = None
            pubdate_elem = root.find(".//dcterms:created", ns)
            if pubdate_elem is not None:
                date_str = pubdate_elem.get(
                    "{http://www.w3.org/2001/XMLSchema-instance}type"
                )
                if date_str and "dateTime" in date_str:
                    date_value = pubdate_elem.text
                    if date_value:
                        pubdate = self._parse_iso_date(date_value)

            # Extract modified date
            modified = None
            modified_elem = root.find(".//dcterms:modified", ns)
            if modified_elem is not None:
                date_value = modified_elem.text
                if date_value:
                    modified = self._parse_iso_date(date_value)

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

    def _parse_app_properties(
        self, xml_content: bytes, original_filename: str
    ) -> BookMetadata:
        """Parse app properties XML (fallback if core.xml not available).

        Parameters
        ----------
        xml_content : bytes
            XML content from docProps/app.xml.
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
                "": "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
            }

            # Extract title
            title_elem = root.find(".//Title", ns)
            title = (
                title_elem.text.strip()
                if title_elem is not None and title_elem.text
                else self._extract_title_from_filename(original_filename)
            )

            return BookMetadata(title=title, author="Unknown")
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
                if "+" in date_str or date_str.count("-") > 2:
                    # Has timezone offset, try to parse
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
