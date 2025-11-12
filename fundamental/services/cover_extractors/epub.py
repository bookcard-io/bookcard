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

"""Cover art extraction strategy for EPUB files.

Implements EPUB cover extraction following the approach of foliate-js,
supporting EPUB 2 and EPUB 3 cover image detection.
"""

from __future__ import annotations

import zipfile
from contextlib import suppress
from pathlib import Path
from urllib.parse import unquote

from lxml import etree  # type: ignore[attr-defined]

from fundamental.services.cover_extractors.base import CoverExtractionStrategy

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
                return epub_zip.read(cover_path)
            except (KeyError, zipfile.BadZipFile):
                return None

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
            return decoded_href

        # Join opf_dir with cover_href
        cover_path = opf_dir / decoded_href
        # Normalize path (resolve .. and .)
        normalized = cover_path.as_posix()
        # Remove leading ./ if present
        if normalized.startswith("./"):
            normalized = normalized[2:]
        return normalized
