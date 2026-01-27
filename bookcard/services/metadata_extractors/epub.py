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

"""Metadata extraction strategy for EPUB files.

Implements comprehensive EPUB metadata extraction following the approach
of foliate-js, supporting EPUB 2 and EPUB 3 with refinements.

This implementation is based on the EPUB metadata extraction logic from
foliate-js (https://github.com/johnfactotum/foliate-js.git), adapted for
Python and integrated into this project's metadata extraction framework.
"""

from __future__ import annotations  # noqa: I001

import re
import zipfile
from datetime import UTC, datetime

from bookcard.services.book_metadata import BookMetadata, Contributor
from bookcard.services.metadata_extractors.base import MetadataExtractionStrategy
from lxml import etree  # type: ignore[attr-defined]
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

EtreeElement = etree._Element  # noqa: SLF001

# Namespaces
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_DCTERMS = "http://purl.org/dc/terms/"
NS_OPF = "http://www.idpf.org/2007/opf"

# MARC relators mapping (common ones)
MARC_RELATORS = {
    "art": "artist",
    "aut": "author",
    "clr": "colorist",
    "edt": "editor",
    "ill": "illustrator",
    "nrt": "narrator",
    "trl": "translator",
    "pbl": "publisher",
}

# ONIX identifier type codes
ONIX_CODES = {
    "02": "isbn",
    "06": "doi",
    "15": "isbn",
    "26": "doi",
    "34": "issn",
}

# EPUB prefix mappings
PREFIX_MARC = "http://www.loc.gov/marc/relators/"
PREFIX_ONIX = "http://www.editeur.org/ONIX/book/codelists/current.html#"


class EpubMetadataExtractor(MetadataExtractionStrategy):
    """Metadata extraction strategy for EPUB files."""

    def can_handle(self, file_format: str) -> bool:
        """Check if format is EPUB."""
        return file_format.upper().lstrip(".") == "EPUB"

    def extract(self, file_path: Path, original_filename: str) -> BookMetadata:
        """Extract metadata from EPUB file."""
        # EPUB is a ZIP file containing OPF metadata
        try:
            with zipfile.ZipFile(file_path, "r") as epub_zip:
                opf_path = self._find_opf_file(epub_zip)
                if opf_path is None:
                    msg = "No OPF file found in EPUB"
                    raise ValueError(msg)

                root = self._parse_opf(epub_zip, opf_path)
                return self._extract_metadata_from_opf(
                    root, original_filename, opf_path
                )
        except zipfile.BadZipFile as e:
            msg = f"File is not a valid EPUB/ZIP file: {e}"
            raise ValueError(msg) from e

    def _find_opf_file(self, epub_zip: zipfile.ZipFile) -> str | None:
        """Find the OPF file in the EPUB archive."""
        # First try to find container.xml to get the correct OPF path
        try:
            container_content = epub_zip.read("META-INF/container.xml")
            from lxml import etree  # type: ignore[attr-defined]

            parser = etree.XMLParser(resolve_entities=False, no_network=True)
            container = etree.fromstring(container_content, parser=parser)
            ns = {"container": "urn:oasis:names:tc:opendocument:xmlns:container"}
            rootfile = container.find(
                ".//container:rootfile[@media-type='application/oebps-package+xml']", ns
            )
            if rootfile is not None:
                opf_path = rootfile.get("full-path")
                if opf_path:
                    return opf_path
        except (KeyError, ValueError, AttributeError):
            pass

        # Fallback: search for OPF files
        for name in epub_zip.namelist():
            if name.endswith(("content.opf", ".opf")):
                return name
        return None

    def _parse_opf(self, epub_zip: zipfile.ZipFile, opf_path: str) -> EtreeElement:
        """Parse OPF XML from EPUB archive."""
        from lxml import etree  # type: ignore[attr-defined]

        opf_content = epub_zip.read(opf_path)
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        return etree.fromstring(opf_content, parser=parser)

    def _extract_metadata_from_opf(
        self,
        root: EtreeElement,
        _original_filename: str,
        _opf_path: str,
    ) -> BookMetadata:
        """Extract metadata from parsed OPF XML."""
        ns = {
            "dc": NS_DC,
            "opf": NS_OPF,
            "dcterms": NS_DCTERMS,
        }

        # Get base language
        base_lang = (
            (
                root.find(".//opf:metadata", ns).get(
                    "{http://www.w3.org/XML/1998/namespace}lang"
                )
                if root.find(".//opf:metadata", ns) is not None
                else None
            )
            or root.get("{http://www.w3.org/XML/1998/namespace}lang")
            or "und"
        )

        # Extract prefixes for EPUB 3
        prefixes = self._get_prefixes(root)

        # Parse metadata elements
        metadata_elem = root.find(".//opf:metadata", ns)
        if metadata_elem is None:
            # Fallback to root if no metadata element
            metadata_elem = root

        # Group elements by type
        dc_elements = {}
        meta_elements = []
        legacy_meta = {}

        for child in metadata_elem:
            child_ns = etree.QName(child).namespace
            if child_ns == NS_DC:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if tag not in dc_elements:
                    dc_elements[tag] = []
                dc_elements[tag].append(child)
            elif child_ns == NS_OPF and child.tag.endswith("}meta"):
                if child.get("name") and child.get("content"):
                    # EPUB 2 legacy meta
                    legacy_meta[child.get("name")] = child.get("content")
                elif child.get("property"):
                    # EPUB 3 meta with property
                    meta_elements.append(child)

        # Build refinements map (EPUB 3)
        refinements = self._build_refinements(metadata_elem, ns, prefixes)

        # Extract fields
        identifier = self._extract_identifier(root, ns)
        title_info = self._extract_title_info(
            dc_elements.get("title", []), refinements, base_lang, legacy_meta
        )
        subtitle = self._extract_subtitle(dc_elements.get("title", []), refinements)
        description = self._extract_description(
            dc_elements.get("description", []), refinements
        )
        publisher = self._extract_publisher(
            dc_elements.get("publisher", []), refinements
        )
        pubdate = self._extract_pubdate(dc_elements.get("date", []), refinements)
        modified = self._extract_modified(
            meta_elements, refinements, dc_elements.get("date", [])
        )
        languages = self._extract_languages(dc_elements.get("language", []))
        tags = self._extract_tags(dc_elements.get("subject", []), refinements)
        identifiers = self._extract_identifiers(
            dc_elements.get("identifier", []), refinements, identifier
        )
        contributors = self._extract_contributors(
            dc_elements.get("creator", []),
            dc_elements.get("contributor", []),
            refinements,
        )
        series_info = self._extract_series(meta_elements, refinements, legacy_meta)
        rights = self._extract_rights(dc_elements.get("rights", []), refinements)

        # Get primary author from contributors or fallback
        author = "Unknown"
        if contributors:
            authors = [
                c.name for c in contributors if c.role == "author" or c.role is None
            ]
            author = " & ".join(authors) if authors else contributors[0].name

        return BookMetadata(
            title=title_info["title"] or "Unknown",
            subtitle=subtitle,
            sort_title=title_info.get("sort_as"),
            author=author,
            description=description,
            tags=tags,
            series=(
                str(series_info["name"])
                if isinstance(series_info.get("name"), str)
                else None
            ),
            series_index=(
                float(series_info["position"])  # type: ignore[invalid-argument-type]
                if isinstance(series_info.get("position"), (int, float, str))
                and str(series_info["position"]).replace(".", "").isdigit()
                else None
            ),
            publisher=publisher,
            pubdate=pubdate,
            modified=modified,
            languages=languages,
            identifiers=identifiers,
            contributors=contributors,
            rights=rights,
        )

    def _get_prefixes(self, root: EtreeElement) -> dict[str, str]:
        """Extract EPUB prefix mappings from root element."""
        prefixes = {}
        prefix_attr = root.get("{http://www.idpf.org/2007/opf}prefix") or root.get(
            "prefix"
        )
        if prefix_attr:
            # Parse prefix attribute: "a11y: http://... marc: http://..."
            for match in re.finditer(r"(\w+):\s*([^\s]+)", prefix_attr):
                prefixes[match.group(1)] = match.group(2)
        return prefixes

    def _build_refinements(
        self,
        metadata_elem: EtreeElement,
        _ns: dict[str, str],
        _prefixes: dict[str, str],
    ) -> dict[str, list[EtreeElement]]:
        """Build map of refinements (EPUB 3 refines attribute)."""
        refinements: dict[str, list[EtreeElement]] = {}
        ns_opf = {"opf": NS_OPF}

        for meta in metadata_elem.findall(".//opf:meta", ns_opf):
            refines = meta.get("refines")
            if refines:
                # Remove # from refines value
                target_id = refines.lstrip("#")
                if target_id not in refinements:
                    refinements[target_id] = []
                refinements[target_id].append(meta)

        return refinements

    def _get_property_value(
        self,
        element: EtreeElement,
        refinements: dict[str, list[EtreeElement]],
        property_name: str,
    ) -> str | None:
        """Get property value from refinements."""
        elem_id = element.get("id")
        if not elem_id or elem_id not in refinements:
            return None

        for refine in refinements[elem_id]:
            prop = refine.get("property")
            if prop and prop.endswith(property_name):
                return self._get_element_text(refine)
        return None

    def _get_element_text(self, element: EtreeElement | None) -> str | None:
        """Get text content from element, normalizing whitespace."""
        if element is None or element.text is None:
            return None
        # Normalize whitespace
        text = " ".join(element.text.split())
        return text if text else None

    def _extract_identifier(self, root: EtreeElement, ns: dict[str, str]) -> str:
        """Extract unique identifier."""
        unique_id = root.get("unique-identifier")
        if unique_id:
            elem = root.find(f".//dc:identifier[@id='{unique_id}']", ns)
            if elem is not None:
                return self._get_element_text(elem) or ""

        # Fallback to first identifier
        elem = root.find(".//dc:identifier", ns)
        return self._get_element_text(elem) or ""

    def _extract_title_info(
        self,
        title_elems: list[EtreeElement],
        refinements: dict[str, list[EtreeElement]],
        _base_lang: str,
        legacy_meta: dict[str, str],
    ) -> dict[str, str | None]:
        """Extract title information."""
        if not title_elems:
            return {"title": "Unknown"}

        # Find main title (or first one)
        main_title = None
        for title_elem in title_elems:
            title_type = self._get_property_value(title_elem, refinements, "title-type")
            if title_type == "main" or main_title is None:
                main_title = title_elem

        if main_title is None:
            main_title = title_elems[0]

        title = self._get_element_text(main_title) or "Unknown"
        sort_as = (
            self._get_property_value(main_title, refinements, "file-as")
            or main_title.get("{http://www.idpf.org/2007/opf}file-as")
            or legacy_meta.get("calibre:title_sort")
        )

        return {"title": title, "sort_as": sort_as}

    def _extract_subtitle(
        self,
        title_elems: list[EtreeElement],
        refinements: dict[str, list[EtreeElement]],
    ) -> str | None:
        """Extract subtitle."""
        for title_elem in title_elems:
            title_type = self._get_property_value(title_elem, refinements, "title-type")
            if title_type == "subtitle":
                return self._get_element_text(title_elem)
        return None

    def _extract_description(
        self,
        desc_elems: list[EtreeElement],
        _refinements: dict[str, list[EtreeElement]],
    ) -> str:
        """Extract description."""
        if not desc_elems:
            return ""
        return self._get_element_text(desc_elems[0]) or ""

    def _extract_publisher(
        self, pub_elems: list[EtreeElement], _refinements: dict[str, list[EtreeElement]]
    ) -> str | None:
        """Extract publisher."""
        if not pub_elems:
            return None
        return self._get_element_text(pub_elems[0])

    def _extract_pubdate(
        self,
        date_elems: list[EtreeElement],
        _refinements: dict[str, list[EtreeElement]],
    ) -> datetime | None:
        """Extract publication date."""
        # Look for publication event
        for date_elem in date_elems:
            event = date_elem.get("{http://www.idpf.org/2007/opf}event")
            if event == "publication":
                return self._parse_date(self._get_element_text(date_elem))

        # Fallback to first date
        if date_elems:
            return self._parse_date(self._get_element_text(date_elems[0]))
        return None

    def _extract_modified(
        self,
        meta_elems: list[EtreeElement],
        _refinements: dict[str, list[EtreeElement]],
        date_elems: list[EtreeElement],
    ) -> datetime | None:
        """Extract modification date."""
        # Check meta elements for dcterms:modified
        for meta in meta_elems:
            prop = meta.get("property")
            if prop and ("modified" in prop or prop.endswith("modified")):
                return self._parse_date(self._get_element_text(meta))

        # Check date elements for modification event
        for date_elem in date_elems:
            event = date_elem.get("{http://www.idpf.org/2007/opf}event")
            if event == "modification":
                return self._parse_date(self._get_element_text(date_elem))

        return None

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse date string to datetime."""
        if not date_str:
            return None

        # Try various date formats
        date_str = date_str.strip()
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d",
            "%Y-%m",
            "%Y",
        ]

        for fmt in formats:
            try:
                if len(date_str) >= len(
                    fmt
                    .replace("%", "")
                    .replace("T", "")
                    .replace("Z", "")
                    .replace(":", "")
                    .replace("-", "")
                ):
                    return datetime.strptime(
                        date_str[
                            : len(
                                fmt
                                .replace("%", "")
                                .replace("T", "")
                                .replace("Z", "")
                                .replace(":", "")
                                .replace("-", "")
                            )
                        ],
                        fmt,
                    ).replace(tzinfo=UTC)
            except (ValueError, TypeError):
                continue

        return None

    def _extract_languages(self, lang_elems: list[EtreeElement]) -> list[str]:
        """Extract languages."""
        languages = []
        for lang_elem in lang_elems:
            lang = self._get_element_text(lang_elem)
            if lang:
                languages.append(lang)
        return languages if languages else []

    def _extract_tags(
        self,
        subject_elems: list[EtreeElement],
        _refinements: dict[str, list[EtreeElement]],
    ) -> list[str]:
        """Extract tags (subjects)."""
        tags = []
        for subject_elem in subject_elems:
            tag = self._get_element_text(subject_elem)
            if tag:
                tags.append(tag)
        return tags

    def _extract_identifiers(
        self,
        identifier_elems: list[EtreeElement],
        refinements: dict[str, list[EtreeElement]],
        _main_identifier: str,
    ) -> list[dict[str, str]]:
        """Extract identifiers with normalization."""
        identifiers = []
        seen_types: set[str] = set()

        for ident_elem in identifier_elems:
            ident_val = self._get_element_text(ident_elem)
            if not ident_val:
                continue

            ident_val = ident_val.strip()

            # Get scheme
            scheme = ident_elem.get("scheme", "").lower()

            # Check refinements for identifier-type
            ident_type_prop = self._get_property_value(
                ident_elem, refinements, "identifier-type"
            )
            # Parse ONIX code if present
            if ident_type_prop and PREFIX_ONIX in ident_type_prop:
                code = ident_type_prop.split("#")[-1]
                scheme = ONIX_CODES.get(code, scheme)

            # Normalize identifier
            normalized = self._normalize_identifier(scheme, ident_val)

            # Deduplicate by type
            ident_type = normalized["type"]
            if ident_type not in seen_types:
                seen_types.add(ident_type)
                identifiers.append(normalized)

        return identifiers

    def _normalize_identifier(self, scheme: str, value: str) -> dict[str, str]:
        """Normalize identifier to standard format."""
        # Handle URN format
        if value.lower().startswith("urn:"):
            parts = value[4:].split(":", 1)
            if len(parts) == 2:
                return {"type": parts[0], "val": parts[1]}

        # Handle DOI
        if value.lower().startswith("doi:"):
            return {"type": "doi", "val": value[4:]}

        # Handle ISBN
        if scheme in ("isbn", "") or not scheme:
            clean_isbn = "".join(c for c in value if c.isdigit())
            if len(clean_isbn) == 13:
                return {"type": "isbn13", "val": value}
            if len(clean_isbn) == 10:
                return {"type": "isbn10", "val": value}
            return {"type": "isbn", "val": value}

        # Use scheme as type
        return {"type": scheme or "unknown", "val": value}

    def _extract_contributors(
        self,
        creator_elems: list[EtreeElement],
        contributor_elems: list[EtreeElement],
        refinements: dict[str, list[EtreeElement]],
    ) -> list[Contributor]:
        """Extract contributors with roles."""
        contributors = []

        # Process creators (default to author role)
        for creator_elem in creator_elems:
            name = self._get_element_text(creator_elem)
            if not name:
                continue

            role = self._extract_role(creator_elem, refinements) or "author"
            sort_as = self._get_property_value(
                creator_elem, refinements, "file-as"
            ) or creator_elem.get("{http://www.idpf.org/2007/opf}file-as")

            contributors.append(Contributor(name=name, role=role, sort_as=sort_as))

        # Process contributors
        for contrib_elem in contributor_elems:
            name = self._get_element_text(contrib_elem)
            if not name:
                continue

            role = self._extract_role(contrib_elem, refinements) or "contributor"
            sort_as = self._get_property_value(
                contrib_elem, refinements, "file-as"
            ) or contrib_elem.get("{http://www.idpf.org/2007/opf}file-as")

            contributors.append(Contributor(name=name, role=role, sort_as=sort_as))

        return contributors

    def _extract_role(
        self, element: EtreeElement, refinements: dict[str, list[EtreeElement]]
    ) -> str | None:
        """Extract role from element or refinements."""
        # Check refinements for role property
        role_prop = self._get_property_value(element, refinements, "role")
        if role_prop:
            # Check if it's a MARC relator
            if PREFIX_MARC in role_prop:
                relator_code = role_prop.split("/")[-1]
                return MARC_RELATORS.get(relator_code)
            # Direct role value
            return role_prop

        # Check opf:role attribute (EPUB 2/3.1)
        opf_role = element.get("{http://www.idpf.org/2007/opf}role")
        if opf_role:
            return MARC_RELATORS.get(opf_role, opf_role)

        return None

    def _extract_series(
        self,
        meta_elems: list[EtreeElement],
        refinements: dict[str, list[EtreeElement]],
        legacy_meta: dict[str, str],
    ) -> dict[str, str | float | None]:
        """Extract series information."""
        # Check for belongs-to-collection property (EPUB 3)
        for meta in meta_elems:
            prop = meta.get("property")
            if prop and "belongs-to-collection" in prop:
                collection_type = self._get_property_value(
                    meta, refinements, "collection-type"
                )
                if collection_type == "series":
                    series_name = self._get_element_text(meta)
                    position = self._get_property_value(
                        meta, refinements, "group-position"
                    )
                    if series_name:
                        return {
                            "name": series_name,
                            "position": float(position)
                            if position and position.replace(".", "").isdigit()
                            else None,
                        }

        # Check legacy Calibre meta (EPUB 2)
        if "calibre:series" in legacy_meta:
            series_name = legacy_meta["calibre:series"]
            series_index = legacy_meta.get("calibre:series_index")
            return {
                "name": series_name,
                "position": float(series_index)
                if series_index
                and series_index.replace(".", "").replace("-", "").isdigit()
                else None,
            }

        return {"name": None, "position": None}

    def _extract_rights(
        self,
        rights_elems: list[EtreeElement],
        _refinements: dict[str, list[EtreeElement]],
    ) -> str | None:
        """Extract rights information."""
        if not rights_elems:
            return None
        return self._get_element_text(rights_elems[0])
