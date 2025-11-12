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

"""Cover art extraction strategy for FB2 (FictionBook 2.0) files.

Extracts cover image from FB2 files by finding coverpage image element,
following the approach of foliate-js.
"""

from __future__ import annotations

import base64
import binascii
import re
from typing import TYPE_CHECKING

from lxml import etree  # type: ignore[attr-defined]

from fundamental.services.cover_extractors.base import CoverExtractionStrategy

if TYPE_CHECKING:
    from pathlib import Path


class Fb2CoverExtractor(CoverExtractionStrategy):
    """Cover extraction strategy for FB2 files."""

    def can_handle(self, file_format: str) -> bool:
        """Check if format is FB2."""
        return file_format.upper().lstrip(".") == "FB2"

    def extract_cover(self, file_path: Path) -> bytes | None:
        """Extract cover image from FB2 file.

        Parameters
        ----------
        file_path : Path
            Path to the FB2 file.

        Returns
        -------
        bytes | None
            Cover image data as bytes, or None if no cover found.
        """
        try:
            # Parse XML
            parser = etree.XMLParser(resolve_entities=False, no_network=True)
            tree = etree.parse(str(file_path), parser=parser)
            root = tree.getroot()

            # FB2 namespace (usually empty, but check for it)
            ns = {"fb2": root.nsmap.get(None, "")} if root.nsmap else {}

            # Find coverpage image (following foliate-js: $('coverpage image'))
            coverpage_image = root.find(".//coverpage/image", ns)
            if coverpage_image is None:
                return None

            # Get image source (following foliate-js: converter.getImageSrc)
            href = coverpage_image.get("{http://www.w3.org/1999/xlink}href")
            if not href:
                # Try without namespace
                href = coverpage_image.get("href")
            if not href:
                return None

            # Remove # prefix if present
            if href.startswith("#"):
                href = href[1:]

            # Find binary element with this id
            binary = root.find(f".//binary[@id='{href}']", ns)
            if binary is None:
                return None

            # Extract base64 content
            content = binary.text
            if not content:
                return None

            # Decode base64
            try:
                # Remove whitespace
                content = re.sub(r"\s+", "", content)
                return base64.b64decode(content)
            except (ValueError, TypeError, binascii.Error):
                return None
        except (etree.XMLSyntaxError, AttributeError, ValueError, OSError):
            return None
