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

"""Metadata extraction strategy for OPDS (Open Publication Distribution System) files.

Implements OPDS metadata extraction following the approach of foliate-js.
OPDS is an Atom XML-based format for ebook catalogs and feeds.

This implementation is based on the OPDS metadata extraction logic from
foliate-js (https://github.com/johnfactotum/foliate-js.git), adapted for
Python and integrated into this project's metadata extraction framework.
"""

from __future__ import annotations

import html
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fundamental.services.book_metadata import BookMetadata, Contributor
from fundamental.services.metadata_extractors.base import MetadataExtractionStrategy

if TYPE_CHECKING:
    from pathlib import Path

    from lxml import etree  # type: ignore[attr-defined]

    EtreeElement = etree._Element  # noqa: SLF001

# OPDS namespaces
NS_ATOM = "http://www.w3.org/2005/Atom"
NS_OPDS = "http://opds-spec.org/2010/catalog"
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_DCTERMS = "http://purl.org/dc/terms/"


class OpdsMetadataExtractor(MetadataExtractionStrategy):
    """Metadata extraction strategy for OPDS files."""

    def can_handle(self, file_format: str) -> bool:
        """Check if format is OPDS."""
        return file_format.upper().lstrip(".") == "OPDS"

    def extract(self, file_path: Path, original_filename: str) -> BookMetadata:
        """Extract metadata from OPDS file.

        Parameters
        ----------
        file_path : Path
            Path to the OPDS file.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.

        Raises
        ------
        ValueError
            If file is not a valid OPDS file or parsing fails.
        """
        from lxml import etree  # type: ignore[attr-defined]

        # Parse XML
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        try:
            tree = etree.parse(str(file_path), parser=parser)
            root = tree.getroot()
        except etree.XMLSyntaxError as err:
            msg = f"Invalid OPDS XML: {err}"
            raise ValueError(msg) from err

        # Extract metadata from entry (if it's an entry) or feed
        ns = self._get_namespaces(root)
        entry = self._find_entry(root, ns)

        if entry is not None:
            return self._extract_metadata_from_entry(entry, ns, original_filename)

        # If no entry found, try to extract from feed itself
        return self._extract_metadata_from_feed(root, ns, original_filename)

    def _get_namespaces(self, root: EtreeElement) -> dict[str, str]:
        """Get namespace mapping from root element.

        Parameters
        ----------
        root : EtreeElement
            Root element.

        Returns
        -------
        dict[str, str]
            Namespace mapping.
        """
        ns = {}
        if root.nsmap:
            # Check if default namespace is Atom
            default_ns = root.nsmap.get(None)
            if default_ns == NS_ATOM:
                ns["atom"] = NS_ATOM
            # Add other namespaces
            ns.update({prefix: uri for prefix, uri in root.nsmap.items() if prefix})
        return ns

    def _find_entry(
        self, root: EtreeElement, ns: dict[str, str]
    ) -> EtreeElement | None:
        """Find entry element in OPDS document.

        Parameters
        ----------
        root : EtreeElement
            Root element.
        ns : dict[str, str]
            Namespace mapping.

        Returns
        -------
        EtreeElement | None
            Entry element or None.
        """
        # Try to find entry element
        atom_ns = ns.get("atom") or NS_ATOM
        entries = root.findall(f"{{{atom_ns}}}entry", ns)
        if entries:
            return entries[0]

        # If root is an entry itself
        if root.tag.endswith("}entry") or root.tag == "entry":
            return root

        return None

    def _extract_metadata_from_entry(
        self, entry: EtreeElement, ns: dict[str, str], original_filename: str
    ) -> BookMetadata:
        """Extract metadata from OPDS entry element.

        Parameters
        ----------
        entry : EtreeElement
            Entry element.
        ns : dict[str, str]
            Namespace mapping.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        atom_ns = ns.get("atom") or NS_ATOM
        dc_ns = NS_DC
        dcterms_ns = NS_DCTERMS

        # Title
        title_elem = entry.find(f"{{{atom_ns}}}title", ns)
        title = (
            self._get_text_content(title_elem)
            if title_elem is not None
            else original_filename
        )

        # Authors and contributors
        authors, contributors = self._extract_authors_and_contributors(
            entry, atom_ns, ns
        )
        primary_author = authors[0]["name"] if authors else "Unknown"

        # Publisher
        publisher = self._extract_publisher(entry, dc_ns, dcterms_ns, ns)

        # Publication date
        pubdate = self._extract_pubdate(entry, dc_ns, dcterms_ns, ns)

        # Language
        language = self._extract_language(entry, dc_ns, ns)

        # Identifier
        identifier = self._extract_identifier(entry, dc_ns, ns)

        # Tags
        tags = self._extract_tags(entry, atom_ns, ns)

        # Description
        description = self._extract_description(entry, atom_ns, ns)

        # Rights
        rights = self._extract_rights(entry, atom_ns, ns)

        # Identifiers
        identifiers = self._build_identifiers(identifier)

        # Languages
        languages = [language] if language else []

        return BookMetadata(
            title=title,
            author=primary_author,
            description=description,
            tags=tags,
            publisher=publisher,
            pubdate=pubdate,
            languages=languages,
            identifiers=identifiers,
            contributors=contributors,
            rights=rights,
        )

    def _extract_metadata_from_feed(
        self, root: EtreeElement, ns: dict[str, str], original_filename: str
    ) -> BookMetadata:
        """Extract metadata from OPDS feed element (fallback).

        Parameters
        ----------
        root : EtreeElement
            Feed element.
        ns : dict[str, str]
            Namespace mapping.
        original_filename : str
            Original filename for fallback.

        Returns
        -------
        BookMetadata
            Extracted metadata.
        """
        atom_ns = ns.get("atom") or NS_ATOM

        # Title
        title_elem = root.find(f"{{{atom_ns}}}title", ns)
        title = (
            self._get_text_content(title_elem)
            if title_elem is not None
            else original_filename
        )

        # Subtitle
        subtitle = None
        subtitle_elem = root.find(f"{{{atom_ns}}}subtitle", ns)
        if subtitle_elem is not None:
            subtitle = self._get_text_content(subtitle_elem)

        return BookMetadata(
            title=title,
            subtitle=subtitle,
            author="Unknown",
        )

    def _get_person(
        self, person_elem: EtreeElement, ns: str
    ) -> dict[str, str | None] | None:
        """Extract person information from author/contributor element.

        Parameters
        ----------
        person_elem : EtreeElement
            Person element.
        ns : str
            Namespace URI.

        Returns
        -------
        dict[str, str] | None
            Person info with 'name' and optional 'uri', or None.
        """
        if person_elem is None:
            return None

        name_elem = person_elem.find(f"{{{ns}}}name", {})
        name = self._get_text_content(name_elem) if name_elem is not None else ""

        uri_elem = person_elem.find(f"{{{ns}}}uri", {})
        uri = self._get_text_content(uri_elem) if uri_elem is not None else None

        if not name:
            return None

        return {"name": name, "uri": uri}

    def _extract_authors_and_contributors(
        self, entry: EtreeElement, atom_ns: str, ns: dict[str, str]
    ) -> tuple[list[dict[str, str | None]], list[Contributor]]:
        """Extract authors and contributors from OPDS entry.

        Parameters
        ----------
        entry : EtreeElement
            Entry element.
        atom_ns : str
            Atom namespace URI.
        ns : dict[str, str]
            Namespace mapping.

        Returns
        -------
        tuple[list[dict[str, str | None]], list[Contributor]]
            Tuple of (authors list, contributors list).
        """
        authors = []
        contributors = []

        # Authors
        for author_elem in entry.findall(f"{{{atom_ns}}}author", ns):
            person = self._get_person(author_elem, atom_ns)
            if person:
                authors.append(person)
                contributors.append(
                    Contributor(
                        name=person["name"], role="author", sort_as=person.get("uri")
                    )
                )

        # Contributors
        for contrib_elem in entry.findall(f"{{{atom_ns}}}contributor", ns):
            person = self._get_person(contrib_elem, atom_ns)
            if person:
                contributors.append(
                    Contributor(
                        name=person["name"],
                        role="contributor",
                        sort_as=person.get("uri"),
                    )
                )

        return authors, contributors

    def _extract_publisher(
        self, entry: EtreeElement, dc_ns: str, dcterms_ns: str, ns: dict[str, str]
    ) -> str | None:
        """Extract publisher from OPDS entry.

        Parameters
        ----------
        entry : EtreeElement
            Entry element.
        dc_ns : str
            DC namespace URI.
        dcterms_ns : str
            DCTERMS namespace URI.
        ns : dict[str, str]
            Namespace mapping.

        Returns
        -------
        str | None
            Publisher name or None.
        """
        for _prefix, uri in [(None, dc_ns), ("dc", dc_ns), ("dcterms", dcterms_ns)]:
            pub_elem = entry.find(f"{{{uri}}}publisher", ns)
            if pub_elem is not None:
                return self._get_text_content(pub_elem)
        return None

    def _extract_pubdate(
        self, entry: EtreeElement, dc_ns: str, dcterms_ns: str, ns: dict[str, str]
    ) -> datetime | None:
        """Extract publication date from OPDS entry.

        Parameters
        ----------
        entry : EtreeElement
            Entry element.
        dc_ns : str
            DC namespace URI.
        dcterms_ns : str
            DCTERMS namespace URI.
        ns : dict[str, str]
            Namespace mapping.

        Returns
        -------
        datetime | None
            Publication date or None.
        """
        for _prefix, uri in [("dcterms", dcterms_ns), (None, dc_ns), ("dc", dc_ns)]:
            date_elem = entry.find(f"{{{uri}}}issued", ns) or entry.find(
                f"{{{uri}}}date", ns
            )
            if date_elem is not None:
                date_text = self._get_text_content(date_elem)
                if date_text:
                    return self._parse_date(date_text)
        return None

    def _extract_language(
        self, entry: EtreeElement, dc_ns: str, ns: dict[str, str]
    ) -> str | None:
        """Extract language from OPDS entry.

        Parameters
        ----------
        entry : EtreeElement
            Entry element.
        dc_ns : str
            DC namespace URI.
        ns : dict[str, str]
            Namespace mapping.

        Returns
        -------
        str | None
            Language code or None.
        """
        lang_elem = entry.find(f"{{{dc_ns}}}language", ns)
        return self._get_text_content(lang_elem) if lang_elem is not None else None

    def _extract_identifier(
        self, entry: EtreeElement, dc_ns: str, ns: dict[str, str]
    ) -> str | None:
        """Extract identifier from OPDS entry.

        Parameters
        ----------
        entry : EtreeElement
            Entry element.
        dc_ns : str
            DC namespace URI.
        ns : dict[str, str]
            Namespace mapping.

        Returns
        -------
        str | None
            Identifier or None.
        """
        ident_elem = entry.find(f"{{{dc_ns}}}identifier", ns)
        return self._get_text_content(ident_elem) if ident_elem is not None else None

    def _extract_tags(
        self, entry: EtreeElement, atom_ns: str, ns: dict[str, str]
    ) -> list[str]:
        """Extract tags from categories.

        Parameters
        ----------
        entry : EtreeElement
            Entry element.
        atom_ns : str
            Atom namespace URI.
        ns : dict[str, str]
            Namespace mapping.

        Returns
        -------
        list[str]
            List of tags.
        """
        tags = []
        for category_elem in entry.findall(f"{{{atom_ns}}}category", ns):
            label = category_elem.get("label")
            term = category_elem.get("term")
            if label:
                tags.append(label)
            elif term:
                tags.append(term)
        return tags

    def _extract_description(
        self, entry: EtreeElement, atom_ns: str, ns: dict[str, str]
    ) -> str:
        """Extract description from content or summary.

        Parameters
        ----------
        entry : EtreeElement
            Entry element.
        atom_ns : str
            Atom namespace URI.
        ns : dict[str, str]
            Namespace mapping.

        Returns
        -------
        str
            Description text.
        """
        content_elem = entry.find(f"{{{atom_ns}}}content", ns)
        if content_elem is not None:
            return self._get_content_text(content_elem)

        summary_elem = entry.find(f"{{{atom_ns}}}summary", ns)
        if summary_elem is not None:
            return self._get_content_text(summary_elem)

        return ""

    def _extract_rights(
        self, entry: EtreeElement, atom_ns: str, ns: dict[str, str]
    ) -> str | None:
        """Extract rights from OPDS entry.

        Parameters
        ----------
        entry : EtreeElement
            Entry element.
        atom_ns : str
            Atom namespace URI.
        ns : dict[str, str]
            Namespace mapping.

        Returns
        -------
        str | None
            Rights text or None.
        """
        rights_elem = entry.find(f"{{{atom_ns}}}rights", ns)
        return self._get_text_content(rights_elem) if rights_elem is not None else None

    def _build_identifiers(self, identifier: str | None) -> list[dict[str, str]]:
        """Build identifiers list.

        Parameters
        ----------
        identifier : str | None
            Identifier value.

        Returns
        -------
        list[dict[str, str]]
            List of identifier dictionaries.
        """
        identifiers = []
        if identifier:
            identifiers.append({"type": "opds", "val": identifier})
        return identifiers

    def _get_text_content(self, elem: EtreeElement | None) -> str:
        """Get text content from element.

        Parameters
        ----------
        elem : EtreeElement | None
            Element.

        Returns
        -------
        str
            Text content or empty string.
        """
        if elem is None:
            return ""
        return (elem.text or "").strip()

    def _get_content_text(self, elem: EtreeElement) -> str:
        """Get text content from content/summary element.

        Handles different content types (text, html, xhtml).

        Parameters
        ----------
        elem : EtreeElement
            Content or summary element.

        Returns
        -------
        str
            Extracted text content.
        """
        content_type = elem.get("type", "text")
        if content_type == "xhtml":
            # For XHTML, get all text content
            text_parts = [part.strip() for part in elem.itertext()]
            result = " ".join(text_parts)
            return html.unescape(result)
        if content_type == "html":
            # For HTML, get text content and unescape
            text = (elem.text or "").strip()
            return html.unescape(text)
        # For text, just return text content
        return (elem.text or "").strip()

    def _parse_date(self, date_str: str) -> datetime | None:
        """Parse date string to datetime.

        Parameters
        ----------
        date_str : str
            Date string (ISO 8601 format expected).

        Returns
        -------
        datetime | None
            Parsed datetime or None.
        """
        if not date_str:
            return None

        # Try ISO 8601 formats
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
            "%Y-%m",
            "%Y",
        ]

        for fmt in formats:
            try:
                if len(date_str) >= len(
                    fmt.replace("%", "")
                    .replace("T", "")
                    .replace("Z", "")
                    .replace(":", "")
                    .replace("-", "")
                    .replace("+", "")
                ):
                    return datetime.strptime(date_str[: len(fmt)], fmt).replace(
                        tzinfo=UTC
                    )
            except (ValueError, TypeError):
                continue

        return None
