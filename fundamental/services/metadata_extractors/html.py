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

"""Metadata extraction strategy for HTML and HTMLZ files.

HTMLZ is a ZIP archive containing HTML files (Calibre format).
Extracts metadata from HTML <meta> tags and <title> elements.
"""

from __future__ import annotations

import html
import re
import zipfile
from typing import TYPE_CHECKING

from lxml import etree  # type: ignore[attr-defined]

from fundamental.services.book_metadata import BookMetadata
from fundamental.services.metadata_extractors.base import MetadataExtractionStrategy

if TYPE_CHECKING:
    from pathlib import Path

# HTML meta tag patterns
META_PATTERNS = {
    "title": [
        re.compile(
            r'<meta\s+name=["\']?title["\']?\s+content=["\']([^"\']+)["\']',
            re.IGNORECASE,
        ),
        re.compile(
            r'<meta\s+property=["\']?og:title["\']?\s+content=["\']([^"\']+)["\']',
            re.IGNORECASE,
        ),
        re.compile(
            r'<meta\s+property=["\']?dc:title["\']?\s+content=["\']([^"\']+)["\']',
            re.IGNORECASE,
        ),
    ],
    "author": [
        re.compile(
            r'<meta\s+name=["\']?author["\']?\s+content=["\']([^"\']+)["\']',
            re.IGNORECASE,
        ),
        re.compile(
            r'<meta\s+property=["\']?dc:creator["\']?\s+content=["\']([^"\']+)["\']',
            re.IGNORECASE,
        ),
        re.compile(
            r'<meta\s+name=["\']?creator["\']?\s+content=["\']([^"\']+)["\']',
            re.IGNORECASE,
        ),
    ],
    "description": [
        re.compile(
            r'<meta\s+name=["\']?description["\']?\s+content=["\']([^"\']+)["\']',
            re.IGNORECASE,
        ),
        re.compile(
            r'<meta\s+property=["\']?og:description["\']?\s+content=["\']([^"\']+)["\']',
            re.IGNORECASE,
        ),
        re.compile(
            r'<meta\s+property=["\']?dc:description["\']?\s+content=["\']([^"\']+)["\']',
            re.IGNORECASE,
        ),
    ],
    "publisher": [
        re.compile(
            r'<meta\s+name=["\']?publisher["\']?\s+content=["\']([^"\']+)["\']',
            re.IGNORECASE,
        ),
        re.compile(
            r'<meta\s+property=["\']?dc:publisher["\']?\s+content=["\']([^"\']+)["\']',
            re.IGNORECASE,
        ),
    ],
    "language": [
        re.compile(
            r'<meta\s+http-equiv=["\']?content-language["\']?\s+content=["\']([^"\']+)["\']',
            re.IGNORECASE,
        ),
        re.compile(r'<html\s+lang=["\']([^"\']+)["\']', re.IGNORECASE),
    ],
}


class HtmlMetadataExtractor(MetadataExtractionStrategy):
    """Metadata extraction strategy for HTML and HTMLZ files."""

    def can_handle(self, file_format: str) -> bool:
        """Check if format is HTML or HTMLZ."""
        format_upper = file_format.upper().lstrip(".")
        return format_upper in ("HTML", "HTMLZ")

    def extract(self, file_path: Path, original_filename: str) -> BookMetadata:
        """Extract metadata from HTML or HTMLZ file.

        Parameters
        ----------
        file_path : Path
            Path to the HTML/HTMLZ file.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        if file_path.suffix.lower() == ".htmlz":
            return self._extract_from_htmlz(file_path, original_filename)
        return self._extract_from_html(file_path, original_filename)

    def _extract_from_htmlz(
        self, file_path: Path, original_filename: str
    ) -> BookMetadata:
        """Extract metadata from HTMLZ (ZIP archive).

        Parameters
        ----------
        file_path : Path
            Path to the HTMLZ file.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        try:
            with zipfile.ZipFile(file_path, "r") as htmlz_zip:
                # Find the main HTML file (usually index.html or the first .html file)
                html_files = [
                    f for f in htmlz_zip.namelist() if f.lower().endswith(".html")
                ]
                if not html_files:
                    return self._extract_from_filename(original_filename)

                # Use index.html if available, otherwise first HTML file
                main_html = (
                    "index.html" if "index.html" in html_files else html_files[0]
                )

                html_content = htmlz_zip.read(main_html).decode(
                    "utf-8", errors="ignore"
                )
                return self._parse_html_content(html_content, original_filename)
        except (zipfile.BadZipFile, OSError, KeyError):
            return self._extract_from_filename(original_filename)

    def _extract_from_html(
        self, file_path: Path, original_filename: str
    ) -> BookMetadata:
        """Extract metadata from HTML file.

        Parameters
        ----------
        file_path : Path
            Path to the HTML file.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        try:
            with file_path.open("r", encoding="utf-8", errors="ignore") as html_file:
                content = html_file.read(50000)  # Read first 50KB
                return self._parse_html_content(content, original_filename)
        except (OSError, UnicodeDecodeError):
            return self._extract_from_filename(original_filename)

    def _parse_html_content(
        self, html_content: str, original_filename: str
    ) -> BookMetadata:
        """Parse HTML content to extract metadata.

        Parameters
        ----------
        html_content : str
            HTML content.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        # Try to parse with lxml for better structure
        try:
            parser = etree.HTMLParser(recover=True, encoding="utf-8")
            tree = etree.fromstring(html_content.encode("utf-8"), parser=parser)
            return self._extract_from_tree(tree, original_filename)
        except (etree.XMLSyntaxError, ValueError, AttributeError):
            # Fall back to regex parsing
            return self._extract_with_regex(html_content, original_filename)

    def _extract_from_tree(
        self, tree: etree._Element, original_filename: str
    ) -> BookMetadata:
        """Extract metadata from parsed HTML tree.

        Parameters
        ----------
        tree : etree._Element
            Parsed HTML tree.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        # Extract title
        title = None
        title_elem = tree.find(".//title")
        if title_elem is not None and title_elem.text:
            title = html.unescape(title_elem.text.strip())

        # Extract meta tags
        meta_tags = tree.findall(".//meta")
        metadata: dict[str, str] = {}

        for meta in meta_tags:
            name = meta.get("name", "").lower()
            property_attr = meta.get("property", "").lower()
            content = meta.get("content", "")

            if content:
                if name == "author" or property_attr == "dc:creator":
                    metadata["author"] = html.unescape(content)
                elif name == "description" or property_attr == "dc:description":
                    metadata["description"] = html.unescape(content)
                elif name == "publisher" or property_attr == "dc:publisher":
                    metadata["publisher"] = html.unescape(content)
                elif (property_attr == "og:title" or name == "title") and not title:
                    title = html.unescape(content)

        # Extract language
        html_elem = tree.find(".//html")
        language = None
        if html_elem is not None:
            language = html_elem.get("lang")

        return BookMetadata(
            title=title or self._extract_title_from_filename(original_filename),
            author=metadata.get("author", "Unknown"),
            description=metadata.get("description", ""),
            publisher=metadata.get("publisher"),
            languages=[language] if language else None,
        )

    def _extract_with_regex(
        self, html_content: str, original_filename: str
    ) -> BookMetadata:
        """Extract metadata using regex patterns (fallback).

        Parameters
        ----------
        html_content : str
            HTML content.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        title = self._extract_title_with_regex(html_content, original_filename)
        author = (
            self._extract_field_with_regex(html_content, "author", "Unknown")
            or "Unknown"
        )
        description = (
            self._extract_field_with_regex(html_content, "description", "") or ""
        )
        publisher = self._extract_field_with_regex(html_content, "publisher", None)
        language = self._extract_field_with_regex(html_content, "language", None)

        return BookMetadata(
            title=title,
            author=author,
            description=description,
            publisher=publisher,
            languages=[language] if language else None,
        )

    def _extract_title_with_regex(
        self, html_content: str, original_filename: str
    ) -> str:
        """Extract title from HTML content using regex.

        Parameters
        ----------
        html_content : str
            HTML content.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        str
            Extracted title.
        """
        # Try <title> tag first
        title_match = re.search(
            r"<title[^>]*>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL
        )
        if title_match:
            return html.unescape(re.sub(r"\s+", " ", title_match.group(1)).strip())

        # Try meta tag patterns
        for pattern in META_PATTERNS["title"]:
            match = pattern.search(html_content)
            if match:
                return html.unescape(match.group(1).strip())

        # Fallback to filename
        return self._extract_title_from_filename(original_filename)

    def _extract_field_with_regex(
        self, html_content: str, field_name: str, default: str | None
    ) -> str | None:
        """Extract a metadata field from HTML content using regex patterns.

        Parameters
        ----------
        html_content : str
            HTML content.
        field_name : str
            Field name (e.g., "author", "description", "publisher", "language").
        default : str | None
            Default value if field not found.

        Returns
        -------
        str | None
            Extracted field value or default.
        """
        patterns = META_PATTERNS.get(field_name, [])
        for pattern in patterns:
            match = pattern.search(html_content)
            if match:
                value = match.group(1).strip()
                # Only unescape for non-language fields
                if field_name != "language":
                    value = html.unescape(value)
                return value

        return default

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
