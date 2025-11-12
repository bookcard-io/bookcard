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

"""Metadata extraction strategy for FB2 (FictionBook 2.0) files.

Implements FB2 metadata extraction following the approach of foliate-js.
FB2 is an XML-based ebook format with embedded metadata.

This implementation is based on the FB2 metadata extraction logic from
foliate-js (https://github.com/johnfactotum/foliate-js.git), adapted for
Python and integrated into this project's metadata extraction framework.
"""

from __future__ import annotations

import html
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fundamental.services.book_metadata import BookMetadata, Contributor
from fundamental.services.metadata_extractors.base import MetadataExtractionStrategy

if TYPE_CHECKING:
    from pathlib import Path

    from lxml import etree  # type: ignore[attr-defined]

    EtreeElement = etree._Element  # noqa: SLF001


class Fb2MetadataExtractor(MetadataExtractionStrategy):
    """Metadata extraction strategy for FB2 files."""

    def can_handle(self, file_format: str) -> bool:
        """Check if format is FB2."""
        return file_format.upper().lstrip(".") == "FB2"

    def extract(self, file_path: Path, original_filename: str) -> BookMetadata:
        """Extract metadata from FB2 file.

        Parameters
        ----------
        file_path : Path
            Path to the FB2 file.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.

        Raises
        ------
        ValueError
            If file is not a valid FB2 file or parsing fails.
        """
        from lxml import etree  # type: ignore[attr-defined]

        # Parse XML
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        try:
            tree = etree.parse(str(file_path), parser=parser)
            root = tree.getroot()
        except etree.XMLSyntaxError as err:
            msg = f"Invalid FB2 XML: {err}"
            raise ValueError(msg) from err

        # FB2 namespace (usually empty, but check for it)
        ns = {"fb2": root.nsmap.get(None, "")} if root.nsmap else {}

        # Extract metadata
        return self._extract_metadata(root, ns, original_filename)

    def _extract_metadata(
        self, root: EtreeElement, ns: dict[str, str], original_filename: str
    ) -> BookMetadata:
        """Extract metadata from parsed FB2 XML.

        Parameters
        ----------
        root : EtreeElement
            Root element of FB2 XML.
        ns : dict[str, str]
            Namespace mapping.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """

        # Helper functions
        def find_text(path: str) -> str:
            """Find text content of element."""
            elem = root.find(path, ns)
            return (
                self._normalize_whitespace(elem.text)
                if elem is not None and elem.text
                else ""
            )

        def find_all(path: str) -> list[EtreeElement]:
            """Find all matching elements."""
            return root.findall(path, ns)

        # Title
        title = find_text(".//title-info/book-title") or original_filename

        # Identifier
        identifier = find_text(".//document-info/id")

        # Language
        language = find_text(".//title-info/lang")

        # Authors and contributors
        authors, contributors = self._extract_authors_and_contributors(root, ns)
        primary_author = authors[0]["name"] if authors else "Unknown"

        # Publisher
        publisher = find_text(".//publish-info/publisher")

        # Publication date
        pubdate = self._extract_date(root.find(".//title-info/date", ns))

        # Modified date
        modified = self._extract_date(root.find(".//document-info/date", ns))

        # Description
        description = self._extract_description(root, ns)

        # Tags
        tags = self._extract_tags(root, ns)

        # Identifiers
        identifiers = self._extract_identifiers(identifier)

        # Languages
        languages = [language] if language else []

        return BookMetadata(
            title=title,
            author=primary_author,
            description=description,
            tags=tags,
            publisher=publisher,
            pubdate=pubdate,
            modified=modified,
            languages=languages,
            identifiers=identifiers,
            contributors=contributors,
        )

    def _get_person(self, person_elem: EtreeElement) -> dict[str, str | None] | None:
        """Extract person information from author/translator element.

        Parameters
        ----------
        person_elem : EtreeElement
            Person element (author, translator, etc.).

        Returns
        -------
        dict[str, str] | None
            Person info with 'name' and optional 'sort_as', or None.
        """
        if person_elem is None:
            return None

        # Check for nickname first
        nickname_elem = person_elem.find("nickname")
        if nickname_elem is not None and nickname_elem.text:
            name = self._normalize_whitespace(nickname_elem.text)
            return {"name": name, "sort_as": name}

        # Otherwise, construct from first-name, middle-name, last-name
        first = self._normalize_whitespace(
            person_elem.findtext("first-name", default="")
        )
        middle = self._normalize_whitespace(
            person_elem.findtext("middle-name", default="")
        )
        last = self._normalize_whitespace(person_elem.findtext("last-name", default=""))

        name_parts = [part for part in [first, middle, last] if part]
        if not name_parts:
            return None

        name = " ".join(name_parts)

        # Sort as: "Last, First Middle"
        sort_as = None
        if last:
            first_middle = " ".join([part for part in [first, middle] if part])
            sort_as = f"{last}, {first_middle}" if first_middle else last

        return {"name": name, "sort_as": sort_as}

    def _extract_authors_and_contributors(
        self, root: EtreeElement, ns: dict[str, str]
    ) -> tuple[list[dict[str, str | None]], list[Contributor]]:
        """Extract authors and all contributors from FB2 XML.

        Parameters
        ----------
        root : EtreeElement
            Root element of FB2 XML.
        ns : dict[str, str]
            Namespace mapping.

        Returns
        -------
        tuple[list[dict[str, str | None]], list[Contributor]]
            Tuple of (authors list, contributors list).
        """
        authors = []
        contributors = []

        # Authors (from title-info)
        for author_elem in root.findall(".//title-info/author", ns):
            person = self._get_person(author_elem)
            if person:
                authors.append(person)
                contributors.append(
                    Contributor(
                        name=person["name"],
                        role="author",
                        sort_as=person.get("sort_as"),
                    )
                )

        # Translators (from title-info)
        for translator_elem in root.findall(".//title-info/translator", ns):
            person = self._get_person(translator_elem)
            if person:
                contributors.append(
                    Contributor(
                        name=person["name"],
                        role="translator",
                        sort_as=person.get("sort_as"),
                    )
                )

        # Additional contributors (from document-info)
        for author_elem in root.findall(".//document-info/author", ns):
            person = self._get_person(author_elem)
            if person:
                contributors.append(
                    Contributor(
                        name=person["name"],
                        role="contributor",
                        sort_as=person.get("sort_as"),
                    )
                )

        # Program used (treated as contributor with 'bkp' role)
        for program_elem in root.findall(".//document-info/program-used", ns):
            program_text = (
                self._normalize_whitespace(program_elem.text)
                if program_elem.text
                else ""
            )
            if program_text:
                contributors.append(Contributor(name=program_text, role="bkp"))

        return authors, contributors

    def _extract_description(self, root: EtreeElement, ns: dict[str, str]) -> str:
        """Extract description from annotation.

        Parameters
        ----------
        root : EtreeElement
            Root element of FB2 XML.
        ns : dict[str, str]
            Namespace mapping.

        Returns
        -------
        str
            Description text.
        """
        annotation_elem = root.find(".//title-info/annotation", ns)
        if annotation_elem is not None:
            return self._extract_annotation_text(annotation_elem)
        return ""

    def _extract_tags(self, root: EtreeElement, ns: dict[str, str]) -> list[str]:
        """Extract tags from genres.

        Parameters
        ----------
        root : EtreeElement
            Root element of FB2 XML.
        ns : dict[str, str]
            Namespace mapping.

        Returns
        -------
        list[str]
            List of genre tags.
        """
        tags = []
        for genre_elem in root.findall(".//title-info/genre", ns):
            genre_text = (
                self._normalize_whitespace(genre_elem.text) if genre_elem.text else ""
            )
            if genre_text:
                tags.append(genre_text)
        return tags

    def _extract_identifiers(self, identifier: str) -> list[dict[str, str]]:
        """Extract identifiers.

        Parameters
        ----------
        identifier : str
            FB2 identifier.

        Returns
        -------
        list[dict[str, str]]
            List of identifier dictionaries.
        """
        identifiers = []
        if identifier:
            identifiers.append({"type": "fb2", "val": identifier})
        return identifiers

    def _extract_date(self, date_elem: EtreeElement | None) -> datetime | None:
        """Extract date from date element.

        Parameters
        ----------
        date_elem : EtreeElement | None
            Date element.

        Returns
        -------
        datetime | None
            Parsed datetime or None.
        """
        if date_elem is None:
            return None

        # Try value attribute first
        value_attr = date_elem.get("value")
        if value_attr:
            return self._parse_date(value_attr)

        # Fallback to text content
        date_text = self._normalize_whitespace(date_elem.text) if date_elem.text else ""
        if date_text:
            return self._parse_date(date_text)

        return None

    def _parse_date(self, date_str: str) -> datetime | None:
        """Parse date string to datetime.

        Parameters
        ----------
        date_str : str
            Date string.

        Returns
        -------
        datetime | None
            Parsed datetime or None.
        """
        if not date_str:
            return None

        # Try common date formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m",
            "%Y",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%d.%m.%Y",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                if len(date_str) >= len(
                    fmt.replace("%", "")
                    .replace("T", "")
                    .replace("Z", "")
                    .replace(".", "")
                    .replace("/", "")
                ):
                    return datetime.strptime(date_str[: len(fmt)], fmt).replace(
                        tzinfo=UTC
                    )
            except (ValueError, TypeError):
                continue

        return None

    def _extract_annotation_text(self, annotation_elem: EtreeElement) -> str:
        """Extract text from annotation element.

        Parameters
        ----------
        annotation_elem : EtreeElement
            Annotation element.

        Returns
        -------
        str
            Extracted text (simplified - just text content, not HTML).
        """
        # Get all text content from annotation
        text_parts = []
        for elem in annotation_elem.iter():
            if elem.text:
                text_parts.append(self._normalize_whitespace(elem.text))
            if elem.tail:
                text_parts.append(self._normalize_whitespace(elem.tail))

        result = " ".join(text_parts)
        return html.unescape(result)

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Normalize whitespace in text.

        Parameters
        ----------
        text : str
            Text to normalize.

        Returns
        -------
        str
            Normalized text.
        """
        if not text:
            return ""
        # Replace all whitespace sequences with single space
        text = re.sub(r"[\t\n\f\r ]+", " ", text)
        return text.strip()
