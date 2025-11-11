# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Metadata extraction strategy for PDF files.

Implements comprehensive PDF metadata extraction following the approach
of foliate-js, supporting both XMP metadata (Dublin Core) and Info dictionary.

This implementation is based on the PDF metadata extraction logic from
foliate-js (https://github.com/johnfactotum/foliate-js.git), adapted for
Python and integrated into this project's metadata extraction framework.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pypdf import PdfReader

from fundamental.services.book_metadata import BookMetadata, Contributor
from fundamental.services.metadata_extractors.base import MetadataExtractionStrategy

if TYPE_CHECKING:
    from pathlib import Path


class PdfMetadataExtractor(MetadataExtractionStrategy):
    """Metadata extraction strategy for PDF files."""

    def can_handle(self, file_format: str) -> bool:
        """Check if format is PDF."""
        return file_format.upper().lstrip(".") == "PDF"

    def extract(self, file_path: Path, original_filename: str) -> BookMetadata:
        """Extract metadata from PDF file.

        Extracts metadata from both XMP (Dublin Core) and Info dictionary,
        following foliate-js approach.
        """
        with file_path.open("rb") as pdf_file:
            reader = PdfReader(pdf_file)
            info = reader.metadata

            if info is None:
                # Fallback to filename if no metadata
                return BookMetadata(
                    title=original_filename,
                    author="Unknown",
                )

            # Try to get XMP metadata (Dublin Core)
            xmp_metadata = None
            try:
                if hasattr(reader, "xmp_metadata") and reader.xmp_metadata:
                    xmp_metadata = reader.xmp_metadata
            except (AttributeError, KeyError, TypeError):
                pass

            # Extract fields (prefer XMP, fallback to Info)
            # Following foliate-js pattern: metadata?.get('dc:title') ?? info?.Title
            title = (
                self._get_xmp_field(xmp_metadata, "dc:title")
                or info.get("/Title")
                or original_filename
            )
            author = (
                self._get_xmp_field(xmp_metadata, "dc:creator")
                or info.get("/Author")
                or "Unknown"
            )
            description = (
                self._get_xmp_field(xmp_metadata, "dc:description")
                or info.get("/Subject")
                or ""
            )
            publisher = self._get_xmp_field(xmp_metadata, "dc:publisher") or info.get(
                "/Producer"
            )
            language = self._get_xmp_field(xmp_metadata, "dc:language")
            subject = self._get_xmp_field(xmp_metadata, "dc:subject")
            identifier = self._get_xmp_field(xmp_metadata, "dc:identifier")
            rights = self._get_xmp_field(xmp_metadata, "dc:rights")

            # Extract contributors
            contributors = self._extract_contributors(xmp_metadata, info)

            # Extract tags (from Keywords in Info or dc:subject in XMP)
            tags = self._extract_tags(info, subject)

            # Extract dates
            pubdate = self._extract_pubdate(info)
            modified = self._extract_modified(info)

            # Extract identifiers
            identifiers = self._extract_identifiers(identifier)

            # Get primary author from contributors or fallback
            primary_author = author
            if contributors:
                authors = [
                    c.name for c in contributors if c.role == "author" or c.role is None
                ]
                if authors:
                    primary_author = " & ".join(authors)
                elif not primary_author or primary_author == "Unknown":
                    primary_author = contributors[0].name

            return BookMetadata(
                title=title,
                author=primary_author,
                description=description,
                tags=tags,
                publisher=publisher,
                pubdate=pubdate,
                modified=modified,
                languages=[language] if language else [],
                identifiers=identifiers,
                contributors=contributors,
                rights=rights,
            )

    def _get_xmp_field(self, xmp_metadata: object | None, dc_field: str) -> str | None:
        """Get field from XMP metadata (Dublin Core).

        pypdf's xmp_metadata is an XmpInformation object with attributes like
        dc_title, dc_creator, etc. This method extracts values from these attributes.

        Parameters
        ----------
        xmp_metadata : object | None
            XMP metadata (XmpInformation object from pypdf).
        dc_field : str
            Dublin Core field name (e.g., 'dc:title', 'dc:creator').

        Returns
        -------
        str | None
            Field value or None if not found.
        """
        if not xmp_metadata:
            return None

        # Convert dc:title -> dc_title, dc:creator -> dc_creator, etc.
        field_name = dc_field.replace("dc:", "dc_")

        try:
            # pypdf's XmpInformation exposes fields as attributes
            # e.g., xmp_metadata.dc_title, xmp_metadata.dc_creator
            if hasattr(xmp_metadata, field_name):
                value = getattr(xmp_metadata, field_name)
                return self._normalize_xmp_value(value)

            # Also try as dictionary (fallback)
            if isinstance(xmp_metadata, dict):
                if dc_field in xmp_metadata:
                    return self._normalize_xmp_value(xmp_metadata[dc_field])
                if field_name in xmp_metadata:
                    return self._normalize_xmp_value(xmp_metadata[field_name])

        except (AttributeError, KeyError, TypeError):
            pass

        return None

    @staticmethod
    def _normalize_xmp_value(value: object) -> str | None:
        """Normalize XMP metadata value to string.

        Parameters
        ----------
        value : object
            XMP metadata value (can be list, dict, or string).

        Returns
        -------
        str | None
            Normalized string value or None.
        """
        if value is None:
            return None

        if isinstance(value, list):
            # Take first non-empty value
            for item in value:
                if item:
                    return str(item).strip()
            return None

        if isinstance(value, dict):
            # Try common dict patterns
            for key in ["value", "text", "content"]:
                try:
                    val = value.get(key)  # type: ignore[call-overload]
                    if val:
                        return str(val).strip()
                except (KeyError, TypeError):
                    continue

        result = str(value).strip()
        return result if result else None

    def _extract_contributors(
        self, xmp_metadata: object | None, info: dict
    ) -> list[Contributor]:
        """Extract contributors from PDF metadata."""
        contributors = []

        # Get contributor from XMP
        contributor_name = self._get_xmp_field(xmp_metadata, "dc:contributor")
        if contributor_name:
            contributors.extend(
                self._parse_contributor_list(contributor_name, "contributor")
            )

        # Get creator from XMP (as author)
        creator_name = self._get_xmp_field(xmp_metadata, "dc:creator")
        if creator_name:
            contributors.extend(self._parse_contributor_list(creator_name, "author"))
        elif info.get("/Author"):
            # Fallback to Info dictionary
            author_name = info.get("/Author")
            if author_name:
                contributors.append(Contributor(name=author_name, role="author"))

        return contributors

    @staticmethod
    def _parse_contributor_list(names: str, role: str) -> list[Contributor]:
        """Parse comma-separated contributor names into Contributor objects."""
        if not names:
            return []
        if isinstance(names, str) and "," in names:
            return [
                Contributor(name=name.strip(), role=role)
                for name in names.split(",")
                if name.strip()
            ]
        return [Contributor(name=str(names), role=role)]

    def _extract_tags(self, info: dict, dc_subject: str | None) -> list[str]:
        """Extract tags from PDF keywords or dc:subject."""
        tags = []

        # From Keywords in Info dictionary
        keywords = info.get("/Keywords", "")
        if keywords:
            tags.extend([k.strip() for k in keywords.split(",") if k.strip()])

        # From dc:subject in XMP (if different from Keywords)
        if dc_subject and dc_subject not in tags:
            # dc:subject might be a list or string
            if isinstance(dc_subject, list):
                tags.extend([str(s).strip() for s in dc_subject if s])
            else:
                tags.append(dc_subject.strip())

        return tags

    def _extract_pubdate(self, info: dict) -> datetime | None:
        """Extract publication date from PDF metadata."""
        # Try CreationDate from Info dictionary
        creation_date = info.get("/CreationDate")
        if creation_date:
            parsed = self._parse_pdf_date(creation_date)
            if parsed:
                return parsed

        # Try ModDate as fallback
        mod_date = info.get("/ModDate")
        if mod_date:
            parsed = self._parse_pdf_date(mod_date)
            if parsed:
                return parsed

        return None

    def _extract_modified(self, info: dict) -> datetime | None:
        """Extract modification date from PDF metadata."""
        # Try ModDate from Info dictionary
        mod_date = info.get("/ModDate")
        if mod_date:
            return self._parse_pdf_date(mod_date)

        return None

    def _parse_pdf_date(self, date_str: str) -> datetime | None:
        """Parse PDF date string to datetime.

        PDF dates are in format: D:YYYYMMDDHHmmSSOHH'mm'
        or: YYYYMMDDHHmmSSOHH'mm'
        """
        if not date_str:
            return None

        # Remove 'D:' prefix if present
        date_str = date_str.lstrip("D:")

        # Extract date part (YYYYMMDD)
        if len(date_str) >= 8:
            try:
                date_part = date_str[:8]
                year = int(date_part[:4])
                month = int(date_part[4:6])
                day = int(date_part[6:8])

                # Validate date
                if 1 <= month <= 12 and 1 <= day <= 31:
                    return datetime(year, month, day, tzinfo=UTC)
            except (ValueError, TypeError):
                pass

        # Try ISO format
        try:
            # Remove timezone info for simple parsing
            iso_str = date_str.split("+")[0].split("-")[0].split("Z")[0]
            if len(iso_str) >= 10:
                return datetime.strptime(iso_str[:10], "%Y-%m-%d").replace(tzinfo=UTC)
        except (ValueError, TypeError):
            pass

        return None

    def _extract_identifiers(self, dc_identifier: str | None) -> list[dict[str, str]]:
        """Extract identifiers from PDF metadata."""
        identifiers = []

        # From XMP dc:identifier
        if dc_identifier:
            # Try to detect identifier type
            ident_type = "unknown"
            ident_val = str(dc_identifier).strip()

            # Check for common identifier patterns
            if ident_val.lower().startswith("urn:"):
                parts = ident_val[4:].split(":", 1)
                if len(parts) == 2:
                    ident_type = parts[0]
                    ident_val = parts[1]
            elif ident_val.lower().startswith("doi:"):
                ident_type = "doi"
                ident_val = ident_val[4:]
            else:
                # Check if it looks like ISBN
                clean_isbn = "".join(c for c in ident_val if c.isdigit())
                if len(clean_isbn) == 13:
                    ident_type = "isbn13"
                elif len(clean_isbn) == 10:
                    ident_type = "isbn10"

            identifiers.append({"type": ident_type, "val": ident_val})

        return identifiers
