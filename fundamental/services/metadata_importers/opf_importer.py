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

"""OPF format importer for book metadata."""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime

from lxml import etree  # type: ignore[attr-defined]

from fundamental.api.schemas.books import BookUpdate
from fundamental.services.metadata_importers.base import MetadataImporter

# OPF namespaces
NS_OPF = "http://www.idpf.org/2007/opf"
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_DCTERMS = "http://purl.org/dc/terms/"


class OpfImporter(MetadataImporter):
    """Importer for OPF (Open Packaging Format) XML metadata.

    Follows SRP by focusing solely on OPF format import.
    """

    def can_handle(self, format_type: str) -> bool:
        """Check if this importer can handle OPF format.

        Parameters
        ----------
        format_type : str
            Format type identifier.

        Returns
        -------
        bool
            True if format is 'opf'.
        """
        return format_type.lower() == "opf"

    def import_metadata(self, content: str) -> BookUpdate:
        """Import metadata from OPF XML content.

        Parameters
        ----------
        content : str
            OPF XML file content as string.

        Returns
        -------
        BookUpdate
            Book update object ready for form application.

        Raises
        ------
        ValueError
            If XML parsing fails or OPF structure is invalid.
        """
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        try:
            root = etree.fromstring(content.encode("utf-8"), parser=parser)
        except etree.XMLSyntaxError as exc:
            msg = f"Invalid OPF XML format: {exc}"
            raise ValueError(msg) from exc

        ns = {
            "dc": NS_DC,
            "opf": NS_OPF,
            "dcterms": NS_DCTERMS,
        }

        # Find metadata element
        metadata_elem = root.find(".//opf:metadata", ns)
        if metadata_elem is None:
            msg = "OPF file must contain a metadata element"
            raise ValueError(msg)

        return OpfImporter._extract_metadata(metadata_elem, ns)

    @staticmethod
    def _extract_metadata(
        metadata_elem: etree._Element, ns: dict[str, str]
    ) -> BookUpdate:
        """Extract metadata from OPF metadata element.

        Parameters
        ----------
        metadata_elem : etree._Element
            OPF metadata element.
        ns : dict[str, str]
            Namespace mapping.

        Returns
        -------
        BookUpdate
            Book update object.
        """
        update: dict = {}

        OpfImporter._extract_simple_fields(metadata_elem, ns, update)
        OpfImporter._extract_list_fields(metadata_elem, ns, update)
        OpfImporter._extract_identifiers(metadata_elem, ns, update)
        OpfImporter._extract_meta_tag_fields(metadata_elem, ns, update)

        return BookUpdate(**update)

    @staticmethod
    def _extract_simple_fields(
        metadata_elem: etree._Element, ns: dict[str, str], update: dict
    ) -> None:
        """Extract simple text fields from OPF metadata.

        Parameters
        ----------
        metadata_elem : etree._Element
            OPF metadata element.
        ns : dict[str, str]
            Namespace mapping.
        update : dict
            Dictionary to update with extracted fields.
        """
        # Title
        title_elem = metadata_elem.find("dc:title", ns)
        if title_elem is not None and title_elem.text:
            update["title"] = title_elem.text.strip()

        # Publisher
        publisher_elem = metadata_elem.find("dc:publisher", ns)
        if publisher_elem is not None and publisher_elem.text:
            update["publisher_name"] = publisher_elem.text.strip()

        # Description
        desc_elem = metadata_elem.find("dc:description", ns)
        if desc_elem is not None and desc_elem.text:
            update["description"] = desc_elem.text.strip()

        # Publication date
        date_elem = metadata_elem.find("dcterms:date", ns)
        if date_elem is None:
            date_elem = metadata_elem.find("dc:date", ns)
        if date_elem is not None and date_elem.text:
            pubdate = OpfImporter._parse_date(date_elem.text.strip())
            if pubdate:
                update["pubdate"] = pubdate

    @staticmethod
    def _extract_list_fields(
        metadata_elem: etree._Element, ns: dict[str, str], update: dict
    ) -> None:
        """Extract list fields from OPF metadata.

        Parameters
        ----------
        metadata_elem : etree._Element
            OPF metadata element.
        ns : dict[str, str]
            Namespace mapping.
        update : dict
            Dictionary to update with extracted fields.
        """
        # Authors
        creator_elems = metadata_elem.findall("dc:creator", ns)
        if creator_elems:
            authors = [elem.text.strip() for elem in creator_elems if elem.text]
            if authors:
                update["author_names"] = authors

        # Languages
        lang_elems = metadata_elem.findall("dc:language", ns)
        if lang_elems:
            languages = [elem.text.strip() for elem in lang_elems if elem.text]
            if languages:
                update["language_codes"] = languages

        # Tags/Subjects
        subject_elems = metadata_elem.findall("dc:subject", ns)
        if subject_elems:
            tags = [elem.text.strip() for elem in subject_elems if elem.text]
            if tags:
                update["tag_names"] = tags

    @staticmethod
    def _extract_identifiers(
        metadata_elem: etree._Element, ns: dict[str, str], update: dict
    ) -> None:
        """Extract identifiers from OPF metadata.

        Parameters
        ----------
        metadata_elem : etree._Element
            OPF metadata element.
        ns : dict[str, str]
            Namespace mapping.
        update : dict
            Dictionary to update with extracted fields.
        """
        id_elems = metadata_elem.findall("dc:identifier", ns)
        if not id_elems:
            return

        identifiers = []
        for id_elem in id_elems:
            if not id_elem.text:
                continue

            scheme = id_elem.get("scheme") or id_elem.get(f"{{{NS_OPF}}}scheme", "")
            id_type = scheme.lower() if scheme else "unknown"
            identifiers.append({"type": id_type, "val": id_elem.text.strip()})

        if identifiers:
            update["identifiers"] = identifiers

    @staticmethod
    def _extract_meta_tag_fields(
        metadata_elem: etree._Element, ns: dict[str, str], update: dict
    ) -> None:
        """Extract fields from OPF meta tags.

        Parameters
        ----------
        metadata_elem : etree._Element
            OPF metadata element.
        ns : dict[str, str]
            Namespace mapping.
        update : dict
            Dictionary to update with extracted fields.
        """
        # Series
        series_meta = OpfImporter._find_meta_tag(metadata_elem, ns, "calibre:series")
        if series_meta is not None:
            series_name = OpfImporter._get_meta_content(series_meta)
            if series_name:
                update["series_name"] = series_name

        # Series index
        series_index_meta = OpfImporter._find_meta_tag(
            metadata_elem, ns, "calibre:series_index"
        )
        if series_index_meta is not None:
            series_index_str = OpfImporter._get_meta_content(series_index_meta)
            if series_index_str:
                with contextlib.suppress(ValueError):
                    update["series_index"] = float(series_index_str)

        # Rating
        rating_meta = OpfImporter._find_meta_tag(metadata_elem, ns, "calibre:rating")
        if rating_meta is not None:
            rating_str = OpfImporter._get_meta_content(rating_meta)
            if rating_str:
                with contextlib.suppress(ValueError):
                    rating_value = int(rating_str)
                    update["rating_value"] = max(0, min(5, rating_value))

    @staticmethod
    def _find_meta_tag(
        metadata_elem: etree._Element, ns: dict[str, str], property_name: str
    ) -> etree._Element | None:
        """Find meta tag by property or name attribute.

        Parameters
        ----------
        metadata_elem : etree._Element
            OPF metadata element.
        ns : dict[str, str]
            Namespace mapping.
        property_name : str
            Property or name value to search for.

        Returns
        -------
        etree._Element | None
            Found meta element or None.
        """
        # Try with opf: prefix first
        result = metadata_elem.find(f".//opf:meta[@property='{property_name}']", ns)
        if result is not None:
            return result
        result = metadata_elem.find(f".//opf:meta[@name='{property_name}']", ns)
        if result is not None:
            return result
        # Fallback to default namespace (meta tags without prefix)
        opf_ns = ns.get("opf", NS_OPF)
        result = metadata_elem.find(f".//{{{opf_ns}}}meta[@property='{property_name}']")
        if result is not None:
            return result
        return metadata_elem.find(f".//{{{opf_ns}}}meta[@name='{property_name}']")

    @staticmethod
    def _get_meta_content(meta_elem: etree._Element) -> str | None:
        """Get content from meta element.

        Parameters
        ----------
        meta_elem : etree._Element
            Meta element.

        Returns
        -------
        str | None
            Content value or None.
        """
        return meta_elem.get("content") or (
            meta_elem.text.strip() if meta_elem.text else None
        )

    @staticmethod
    def _parse_date(date_str: str) -> datetime | None:
        """Parse date string to datetime.

        Parameters
        ----------
        date_str : str
            Date string to parse.

        Returns
        -------
        datetime | None
            Parsed datetime or None if invalid.
        """
        if not date_str:
            return None

        # Try ISO format first
        try:
            # Handle Z timezone
            if date_str.endswith("Z"):
                date_str = date_str[:-1] + "+00:00"
            dt = datetime.fromisoformat(date_str)
            # Make timezone-aware if naive
            if dt.tzinfo is None:
                return dt.replace(tzinfo=UTC)
        except (ValueError, AttributeError):
            pass
        else:
            return dt

        # Try common date formats
        date_formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
        ]

        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)  # noqa: DTZ007
                # Make timezone-aware if naive
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=UTC)
            except ValueError:
                continue
            else:
                return dt

        return None
