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

"""Parsers and extractors for release information.

This module provides extensible parsers for indexer responses, following OCP.
"""

import re
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, runtime_checkable
from xml.etree import ElementTree as ET  # noqa: S405

from bookcard.pvr.utils.quality import infer_quality_from_title
from bookcard.pvr.utils.xml_parser import extract_publish_date_from_xml

# Torznab XML namespace
TORZNAB_NS = "{http://torznab.com/schemas/2015/feed}"


@runtime_checkable
class ReleaseFieldExtractor(Protocol):
    """Protocol for extracting a field from a release item."""

    def extract(self, item: ET.Element) -> Any:  # noqa: ANN401
        """Extract field value from item."""
        ...


@dataclass
class NamespaceAwareExtractor:
    """Base class for extractors that need an XML namespace."""

    namespace: str = TORZNAB_NS

    def _get_attribute(self, item: ET.Element, name: str, default: str = "") -> str:
        """Get an attribute value from the namespace."""
        attr_elem = item.find(f".//{self.namespace}attr[@name='{name}']")
        if attr_elem is not None:
            value_attr = attr_elem.get("value")
            if value_attr:
                return value_attr
        return default


class TitleExtractor(ReleaseFieldExtractor):
    """Extracts title."""

    def extract(self, item: ET.Element) -> str | None:
        """Extract title from item."""
        title_elem = item.find("title")
        if title_elem is None or title_elem.text is None:
            return None
        return title_elem.text.strip()


class DownloadUrlExtractor(NamespaceAwareExtractor, ReleaseFieldExtractor):
    """Extracts download URL."""

    def extract(self, item: ET.Element) -> str | None:
        """Extract download URL from item."""
        # Try namespace magneturl attribute first
        magnet_url = self._get_attribute(item, "magneturl")
        if magnet_url:
            return magnet_url

        # Try enclosure URL
        enclosure = item.find("enclosure")
        if enclosure is not None:
            url_attr = enclosure.get("url")
            if url_attr:
                return url_attr

        # Try link element
        link_elem = item.find("link")
        if link_elem is not None and link_elem.text:
            return link_elem.text.strip()

        return None


class SizeExtractor(NamespaceAwareExtractor, ReleaseFieldExtractor):
    """Extracts size in bytes."""

    def extract(self, item: ET.Element) -> int | None:
        """Extract size from item."""
        # Try namespace size attribute
        size_str = self._get_attribute(item, "size")
        if size_str:
            try:
                return int(size_str)
            except (ValueError, TypeError):
                pass

        # Try enclosure length
        enclosure = item.find("enclosure")
        if enclosure is not None:
            length_attr = enclosure.get("length")
            if length_attr:
                try:
                    return int(length_attr)
                except (ValueError, TypeError):
                    pass

        return None


class PublishDateExtractor(ReleaseFieldExtractor):
    """Extracts publish date."""

    def extract(self, item: ET.Element) -> datetime | None:
        """Extract publish date from item."""
        return extract_publish_date_from_xml(item)


class GuidExtractor(ReleaseFieldExtractor):
    """Extracts GUID."""

    def extract(self, item: ET.Element) -> str | None:
        """Extract GUID from item."""
        guid_elem = item.find("guid")
        if guid_elem is not None and guid_elem.text:
            return guid_elem.text.strip()
        return None


class AttributeExtractor(NamespaceAwareExtractor, ReleaseFieldExtractor):
    """Extracts a generic attribute from the namespace."""

    def __init__(
        self, attribute_name: str, as_int: bool = False, namespace: str = TORZNAB_NS
    ) -> None:
        super().__init__(namespace)
        self.attribute_name = attribute_name
        self.as_int = as_int

    def extract(self, item: ET.Element) -> str | int | None:
        """Extract attribute value."""
        val = self._get_attribute(item, self.attribute_name)
        if not val:
            return None

        if self.as_int:
            try:
                return int(val)
            except (ValueError, TypeError):
                return None
        return val


class MetadataExtractor(NamespaceAwareExtractor, ReleaseFieldExtractor):
    """Extracts metadata (author, isbn, quality)."""

    def extract(self, item: ET.Element) -> dict[str, Any]:
        """Extract metadata dict."""
        author = self._get_attribute(item, "author") or None
        isbn = self._get_attribute(item, "isbn") or None

        # Extract quality/format
        quality_attr = self._get_attribute(item, "format")

        # We need title for inference if quality is missing
        title_elem = item.find("title")
        title = (
            title_elem.text.strip()
            if title_elem is not None and title_elem.text
            else ""
        )

        quality = quality_attr or infer_quality_from_title(title)

        return {
            "author": author,
            "isbn": isbn,
            "quality": quality,
        }


class AdditionalInfoExtractor(NamespaceAwareExtractor, ReleaseFieldExtractor):
    """Extracts additional info dict."""

    def extract(self, item: ET.Element) -> dict[str, Any]:
        """Extract additional info."""
        additional_info: dict[str, Any] = {}

        infohash = self._get_attribute(item, "infohash")
        if infohash:
            additional_info["infohash"] = infohash

        magnet_url = self._get_attribute(item, "magneturl")
        if magnet_url:
            additional_info["magneturl"] = magnet_url

        return additional_info


class SimpleTextExtractor(ReleaseFieldExtractor):
    """Extracts simple text from a child element."""

    def __init__(self, tag: str) -> None:
        self.tag = tag

    def extract(self, item: ET.Element) -> str | None:
        """Extract text from child element.

        Parameters
        ----------
        item : ET.Element
            XML element to extract from.

        Returns
        -------
        str | None
            Text content of the element, or None if not found.
        """
        elem = item.find(self.tag)
        return elem.text if elem is not None else None


class RssDownloadUrlExtractor(DownloadUrlExtractor):
    """Extracts download URL from RSS items, including description scanning."""

    def extract(self, item: ET.Element) -> str | None:
        """Extract download URL."""
        # Try standard extraction first
        url = super().extract(item)
        if url:
            # Check if it looks like a magnet or torrent if it came from link/enclosure
            # (Standard extractor handles this for attributes/enclosure usually, but scanning descriptions is extra)
            return url

        # Scan description for magnet/torrent links
        desc_elem = item.find("description")
        if desc_elem is not None and desc_elem.text:
            text = desc_elem.text
            # Look for magnet links
            magnet_match = re.search(r"magnet:\?[^\s<>\"']+", text, re.IGNORECASE)
            if magnet_match:
                return magnet_match.group(0)

            # Look for .torrent URLs
            torrent_match = re.search(
                r"https?://[^\s<>\"']+\.torrent", text, re.IGNORECASE
            )
            if torrent_match:
                return torrent_match.group(0)

        return None


class RssSeedersLeechersExtractor(ReleaseFieldExtractor):
    """Extracts seeders and leechers from description."""

    def extract(self, item: ET.Element) -> dict[str, int | None]:
        """Extract seeders/leechers dict."""
        seeders: int | None = None
        leechers: int | None = None

        desc_elem = item.find("description")
        if desc_elem is not None and desc_elem.text:
            description = desc_elem.text
            # Look for common patterns like "Seeders: 5" or "S:5 L:2"
            seeders_match = re.search(
                r"(?:seeders?|seeds?|s)[\s:]+(\d+)", description, re.IGNORECASE
            )
            if seeders_match:
                with suppress(ValueError, TypeError):
                    seeders = int(seeders_match.group(1))

            leechers_match = re.search(
                r"(?:leechers?|leech|peers?|l)[\s:]+(\d+)", description, re.IGNORECASE
            )
            if leechers_match:
                with suppress(ValueError, TypeError):
                    leechers = int(leechers_match.group(1))

        return {"seeders": seeders, "leechers": leechers}


class CompositeReleaseParser:
    """Composite parser that uses multiple extractors."""

    def __init__(self, extractors: dict[str, ReleaseFieldExtractor]) -> None:
        self.extractors = extractors

    def parse(self, item: ET.Element) -> dict[str, Any]:
        """Parse item using registered extractors."""
        result = {}
        for field, extractor in self.extractors.items():
            value = extractor.extract(item)
            if isinstance(value, dict):
                # Flatten dict results into main result if they are metadata/stats
                # This covers MetadataExtractor and RssSeedersLeechersExtractor
                # and AdditionalInfoExtractor
                result.update(value)
            else:
                result[field] = value
        return result
