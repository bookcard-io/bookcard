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

"""Cover art extraction strategy for PDF files.

Renders the first page of the PDF as a cover image, following the approach
of foliate-js.
"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

from fundamental.services.cover_extractors.base import CoverExtractionStrategy

if TYPE_CHECKING:
    from pathlib import Path


class PdfCoverExtractor(CoverExtractionStrategy):
    """Cover extraction strategy for PDF files."""

    def can_handle(self, file_format: str) -> bool:
        """Check if format is PDF."""
        return file_format.upper().lstrip(".") == "PDF"

    def extract_cover(self, file_path: Path) -> bytes | None:
        """Extract cover image from PDF file by rendering first page.

        Parameters
        ----------
        file_path : Path
            Path to the PDF file.

        Returns
        -------
        bytes | None
            Cover image data as bytes (JPEG), or None if extraction fails.
        """
        try:
            # Try to use pdf2image if available (requires poppler)
            # This is optional - if not available, cover extraction for PDF will fail
            from pdf2image import convert_from_path  # type: ignore[import-untyped]

            # Convert first page to image (following foliate-js: renderPage(await pdf.getPage(1)))
            images = convert_from_path(
                str(file_path), first_page=1, last_page=1, dpi=150
            )
            if not images:
                return None
            img = images[0]
            # Convert to RGB if necessary
            if img.mode != "RGB":
                img = img.convert("RGB")
            # Save to bytes as JPEG
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            return buffer.getvalue()
        except ImportError:
            # pdf2image not available - PDF cover extraction requires pdf2image
            # which in turn requires poppler-utils system package
            return None
        except (OSError, ValueError, TypeError, AttributeError):
            return None
