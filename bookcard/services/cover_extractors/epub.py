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

"""Cover art extraction strategy for EPUB files.

Implements EPUB cover extraction following the approach of foliate-js,
supporting EPUB 2 and EPUB 3 cover image detection.
"""

from __future__ import annotations

import posixpath
import zipfile
from contextlib import suppress
from pathlib import Path
from urllib.parse import unquote

from lxml import etree  # type: ignore[attr-defined]

from bookcard.services.cover_extractors.base import CoverExtractionStrategy

# Namespaces
NS_OPF = "http://www.idpf.org/2007/opf"


class EpubCoverExtractor(CoverExtractionStrategy):
    """Cover extraction strategy for EPUB files."""

    def can_handle(self, file_format: str) -> bool:
        """Check if format is EPUB."""
        return file_format.upper().lstrip(".") == "EPUB"

    def extract_cover(self, file_path: Path) -> bytes | None:
        """Extract cover image from EPUB file.

        Parameters
        ----------
        file_path : Path
            Path to the EPUB file.

        Returns
        -------
        bytes | None
            Cover image data as bytes, or None if no cover found.
        """
        with zipfile.ZipFile(file_path, "r") as epub_zip:
            opf_path = self._find_opf_file(epub_zip)
            if opf_path is None:
                return None

            root = self._parse_opf(epub_zip, opf_path)
            opf_dir = Path(opf_path).parent

            # Find cover item using multiple strategies (following foliate-js)
            cover_href = self._find_cover_href(root, opf_dir)

            if cover_href is None:
                return None

            # Resolve relative path from OPF directory
            cover_path = self._resolve_cover_path(cover_href, opf_dir)

            # Extract cover image from EPUB archive
            try:
                data = epub_zip.read(cover_path)
            except (KeyError, zipfile.BadZipFile):
                return None
            else:
                # Check if data looks like HTML/XHTML (starts with tags)
                # Some EPUBs point to an HTML wrapper page instead of the image
                if data.strip().startswith((b"<html", b"<?xml", b"<!DOCTYPE")):
                    return self._extract_image_from_html(data, cover_path, epub_zip)

                return data

    def _find_opf_file(self, epub_zip: zipfile.ZipFile) -> str | None:
        """Find the OPF file in the EPUB archive."""
        # First try to find container.xml to get the correct OPF path
        with suppress(KeyError, ValueError, AttributeError):
            container_content = epub_zip.read("META-INF/container.xml")
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

        # Fallback: search for OPF files
        for name in epub_zip.namelist():
            if name.endswith(("content.opf", ".opf")):
                return name
        return None

    def _parse_opf(self, epub_zip: zipfile.ZipFile, opf_path: str) -> etree._Element:
        """Parse OPF XML from EPUB archive."""
        opf_content = epub_zip.read(opf_path)
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        return etree.fromstring(opf_content, parser=parser)

    def _find_cover_href(self, root: etree._Element, _opf_dir: Path) -> str | None:
        """Find cover image href using multiple strategies.

        Following foliate-js approach:
        1. Look for item with cover-image property
        2. EPUB 2 compat: find meta with name='cover' and get its content (ID)
        3. Look in guide for reference with type including 'cover'
        """
        ns = {"opf": NS_OPF}

        # Strategy 1: Look for item with cover-image property
        manifest = root.find(".//opf:manifest", ns)
        cover_href = self._find_cover_by_property(manifest, ns)
        if cover_href:
            return cover_href

        # Strategy 2: EPUB 2 compat - find meta with name='cover'
        metadata = root.find(".//opf:metadata", ns)
        cover_href = self._find_cover_by_meta(manifest, metadata, ns)
        if cover_href:
            return cover_href

        # Strategy 3: Look in guide for reference with type including 'cover'
        guide = root.find(".//opf:guide", ns)
        return self._find_cover_by_guide(guide, ns)

    def _find_cover_by_property(
        self, manifest: etree._Element | None, ns: dict[str, str]
    ) -> str | None:
        """Find cover by cover-image property."""
        if manifest is None:
            return None
        for item in manifest.findall(".//opf:item", ns):
            properties = item.get("properties", "")
            if "cover-image" in properties:
                href = item.get("href")
                if href:
                    return href
        return None

    def _find_cover_by_meta(
        self,
        manifest: etree._Element | None,
        metadata: etree._Element | None,
        ns: dict[str, str],
    ) -> str | None:
        """Find cover by EPUB 2 meta tag."""
        if metadata is None or manifest is None:
            return None
        for meta in metadata.findall(".//opf:meta", ns):
            if meta.get("name") == "cover":
                cover_id = meta.get("content")
                if cover_id:
                    for item in manifest.findall(".//opf:item", ns):
                        if item.get("id") == cover_id:
                            href = item.get("href")
                            if href:
                                return href
        return None

    def _find_cover_by_guide(
        self, guide: etree._Element | None, ns: dict[str, str]
    ) -> str | None:
        """Find cover by guide reference."""
        if guide is None:
            return None
        for reference in guide.findall(".//opf:reference", ns):
            ref_type = reference.get("type", "")
            if "cover" in ref_type.lower():
                href = reference.get("href")
                if href:
                    return href
        return None

    def _resolve_cover_path(self, cover_href: str, opf_dir: Path) -> str:
        """Resolve cover image path relative to OPF directory.

        Parameters
        ----------
        cover_href : str
            Cover href from OPF (may be URL-encoded).
        opf_dir : Path
            Directory containing the OPF file.

        Returns
        -------
        str
            Resolved path within EPUB archive.
        """
        # Decode URL encoding
        decoded_href = unquote(cover_href)

        # If absolute path (starts with /), resolve from root
        if decoded_href.startswith("/"):
            return decoded_href.lstrip("/")

        # Otherwise, resolve relative to OPF directory
        if opf_dir == Path():
            full_path = decoded_href
        else:
            # Use posixpath for zip file paths
            # opf_dir is a Path object, convert to str using as_posix
            full_path = f"{opf_dir.as_posix()}/{decoded_href}"

        # Normalize path (resolve .. and .)
        normalized = posixpath.normpath(full_path)

        # Remove leading ./ if present (posixpath.normpath might leave it if started with ./)
        if normalized.startswith("./"):
            normalized = normalized[2:]
        return normalized

    def _extract_image_from_html(
        self, html_content: bytes, html_path: str, epub_zip: zipfile.ZipFile
    ) -> bytes | None:
        """Extract image from HTML cover page."""
        try:
            # Use HTML parser to be lenient
            parser = etree.HTMLParser()
            root = etree.fromstring(html_content, parser=parser)
        except (etree.XMLSyntaxError, ValueError, TypeError):
            return None
        else:
            # Try <img> src
            img = root.find(".//img")
            if img is not None:
                src = img.get("src")
                if src:
                    return self._read_image_from_src(src, html_path, epub_zip)

            # Try <image> xlink:href (SVG style)
            image = root.find(".//image")
            if image is not None:
                # etree HTMLParser might lowercase namespaces or tag names
                href = (
                    image.get("href")
                    or image.get("{http://www.w3.org/1999/xlink}href")
                    or image.get("xlink:href")
                )
                if href:
                    return self._read_image_from_src(href, html_path, epub_zip)

            return None

    def _read_image_from_src(
        self, src: str, base_path: str, epub_zip: zipfile.ZipFile
    ) -> bytes | None:
        """Read image file resolving src relative to base_path."""
        try:
            # Resolve path
            decoded_src = unquote(src)
            base_dir = Path(base_path).parent

            image_path = self._resolve_cover_path(decoded_src, base_dir)
            return epub_zip.read(image_path)
        except (KeyError, zipfile.BadZipFile):
            return None
