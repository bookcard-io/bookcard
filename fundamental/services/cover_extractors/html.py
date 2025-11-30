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

"""Cover art extraction strategy for HTML and HTMLZ files.

Extracts cover image from HTML files by finding the first image
or an image marked as cover. For HTMLZ (ZIP archive), extracts
from the main HTML file.
"""

from __future__ import annotations

import re
import zipfile
from io import BytesIO
from typing import TYPE_CHECKING

from PIL import Image  # type: ignore[import-untyped]

from fundamental.services.cover_extractors.base import CoverExtractionStrategy

if TYPE_CHECKING:
    from pathlib import Path


class HtmlCoverExtractor(CoverExtractionStrategy):
    """Cover extraction strategy for HTML and HTMLZ files."""

    def can_handle(self, file_format: str) -> bool:
        """Check if format is HTML or HTMLZ."""
        format_upper = file_format.upper().lstrip(".")
        return format_upper in ("HTML", "HTMLZ")

    def extract_cover(self, file_path: Path) -> bytes | None:
        """Extract cover image from HTML or HTMLZ file.

        Parameters
        ----------
        file_path : Path
            Path to the HTML/HTMLZ file.

        Returns
        -------
        bytes | None
            Cover image data as bytes, or None if no cover found.
        """
        if file_path.suffix.lower() == ".htmlz":
            return self._extract_from_htmlz(file_path)
        return self._extract_from_html(file_path)

    def _extract_from_htmlz(self, file_path: Path) -> bytes | None:
        """Extract cover from HTMLZ (ZIP archive).

        Parameters
        ----------
        file_path : Path
            Path to the HTMLZ file.

        Returns
        -------
        bytes | None
            Cover image data as bytes, or None if no cover found.
        """
        try:
            with zipfile.ZipFile(file_path, "r") as htmlz_zip:
                # Find the main HTML file
                html_files = [
                    f for f in htmlz_zip.namelist() if f.lower().endswith(".html")
                ]
                if not html_files:
                    return None

                main_html = (
                    "index.html" if "index.html" in html_files else html_files[0]
                )
                html_content = htmlz_zip.read(main_html).decode(
                    "utf-8", errors="ignore"
                )

                # Find image in HTML
                image_path = self._find_image_in_html(html_content)
                if not image_path:
                    return None

                # Resolve image path relative to HTML file location
                html_dir = main_html.rsplit("/", 1)[0] if "/" in main_html else ""
                if html_dir:
                    image_path = f"{html_dir}/{image_path}"
                else:
                    image_path = image_path.lstrip("/")

                # Extract image from ZIP
                try:
                    image_data = htmlz_zip.read(image_path)
                    return self._process_image(image_data)
                except KeyError:
                    # Try alternative paths
                    for alt_path in self._try_alternative_paths(image_path, htmlz_zip):
                        try:
                            image_data = htmlz_zip.read(alt_path)
                            return self._process_image(image_data)
                        except KeyError:
                            continue

                return None
        except (zipfile.BadZipFile, OSError, KeyError):
            return None

    def _extract_from_html(self, _file_path: Path) -> bytes | None:
        """Extract cover from HTML file.

        HTML files typically reference external images, so we can't
        extract the actual image data. Return None for standalone HTML.

        Parameters
        ----------
        _file_path : Path
            Path to the HTML file (unused, kept for interface consistency).

        Returns
        -------
        bytes | None
            None (HTML files don't contain embedded images).
        """
        # Standalone HTML files reference external images, not embedded
        # We can't extract cover from standalone HTML without network access
        return None

    def _find_image_in_html(self, html_content: str) -> str | None:
        """Find cover image path in HTML content.

        Parameters
        ----------
        html_content : str
            HTML content.

        Returns
        -------
        str | None
            Image path or None if not found.
        """
        # Look for images with cover-related attributes or class names
        cover_patterns = [
            r'<img[^>]*class=["\'][^"\']*cover[^"\']*["\'][^>]*src=["\']([^"\']+)["\']',
            r'<img[^>]*id=["\'][^"\']*cover[^"\']*["\'][^>]*src=["\']([^"\']+)["\']',
            r'<img[^>]*alt=["\'][^"\']*cover[^"\']*["\'][^>]*src=["\']([^"\']+)["\']',
            r'<img[^>]*src=["\']([^"\']*cover[^"\']*)["\']',
        ]

        for pattern in cover_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return match.group(1)

        # Fallback: find first image
        first_img_match = re.search(
            r'<img[^>]*src=["\']([^"\']+)["\']', html_content, re.IGNORECASE
        )
        if first_img_match:
            return first_img_match.group(1)

        return None

    def _try_alternative_paths(
        self, image_path: str, _zip_file: zipfile.ZipFile
    ) -> list[str]:
        """Try alternative paths for image in ZIP.

        Parameters
        ----------
        image_path : str
            Original image path.
        _zip_file : zipfile.ZipFile
            ZIP file to search in (unused, kept for potential future use).

        Returns
        -------
        list[str]
            List of alternative paths to try.
        """
        alternatives = []
        # Try with different separators
        if "/" in image_path:
            alternatives.append(image_path.replace("/", "\\"))
        if "\\" in image_path:
            alternatives.append(image_path.replace("\\", "/"))
        # Try in common image directories
        for dir_name in ["images", "img", "pictures", "pics", "media"]:
            filename = image_path.split("/")[-1].split("\\")[-1]
            alternatives.append(f"{dir_name}/{filename}")
            alternatives.append(f"{dir_name}\\{filename}")
        return alternatives

    def _process_image(self, image_data: bytes) -> bytes | None:
        """Process image data and convert to JPEG if needed.

        Parameters
        ----------
        image_data : bytes
            Raw image data.

        Returns
        -------
        bytes | None
            JPEG image data as bytes, or None if processing fails.
        """
        try:
            img = Image.open(BytesIO(image_data))
            # Convert to RGB if necessary
            if img.mode != "RGB":
                img = img.convert("RGB")
            # Save to bytes as JPEG
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            return buffer.getvalue()
        except (OSError, ValueError, TypeError, AttributeError):
            return None
