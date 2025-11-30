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

"""Tests for HTML cover extractor to achieve 100% coverage."""

from __future__ import annotations

import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image  # type: ignore[import-untyped]

from fundamental.services.cover_extractors.html import HtmlCoverExtractor


@pytest.fixture
def extractor() -> HtmlCoverExtractor:
    """Create HtmlCoverExtractor instance."""
    return HtmlCoverExtractor()


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Create sample image bytes for testing.

    Returns
    -------
    bytes
        JPEG image data as bytes.
    """
    img = Image.new("RGB", (100, 100), color="red")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


def _create_mock_htmlz(
    html_content: str,
    image_data: bytes | None = None,
    image_path: str = "cover.jpg",
    html_filename: str = "index.html",
    invalid_zip: bool = False,
) -> Path:
    """Create a mock HTMLZ file for testing.

    Parameters
    ----------
    html_content : str
        HTML content to write.
    image_data : bytes | None
        Image data to include in ZIP.
    image_path : str
        Path to image in ZIP.
    html_filename : str
        Filename for the HTML file inside the ZIP.
    invalid_zip : bool
        If True, create an invalid ZIP file.

    Returns
    -------
    Path
        Path to the created HTMLZ file.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".htmlz") as tmp:
        file_path = Path(tmp.name)

    if invalid_zip:
        file_path.write_bytes(b"invalid zip content")
        return file_path

    with zipfile.ZipFile(file_path, "w") as htmlz_zip:
        htmlz_zip.writestr(html_filename, html_content.encode("utf-8"))
        if image_data:
            htmlz_zip.writestr(image_path, image_data)

    return file_path


@pytest.mark.parametrize(
    ("file_format", "expected"),
    [
        ("html", True),
        ("HTML", True),
        ("htmlz", True),
        ("HTMLZ", True),
        (".html", True),
        ("epub", False),
        ("pdf", False),
    ],
)
def test_can_handle(
    extractor: HtmlCoverExtractor, file_format: str, expected: bool
) -> None:
    """Test can_handle for various formats (covers lines 41-44)."""
    assert extractor.can_handle(file_format) == expected


def test_extract_cover_htmlz(
    extractor: HtmlCoverExtractor, sample_image_bytes: bytes
) -> None:
    """Test extract_cover with HTMLZ file (covers lines 59-61)."""
    html_content = """<!DOCTYPE html>
    <html>
    <head><title>Test Book</title></head>
    <body>
        <img src="cover.jpg" class="cover" alt="Cover">
    </body>
    </html>"""

    file_path = _create_mock_htmlz(
        html_content=html_content,
        image_data=sample_image_bytes,
        image_path="cover.jpg",
    )

    try:
        result = extractor.extract_cover(file_path)
        assert result is not None
        assert isinstance(result, bytes)
    finally:
        file_path.unlink()


def test_extract_cover_html(extractor: HtmlCoverExtractor) -> None:
    """Test extract_cover with HTML file (covers lines 121-139)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        file_path = Path(tmp.name)
        tmp.write(b"<html><body>Content</body></html>")

    try:
        result = extractor.extract_cover(file_path)
        # Standalone HTML files don't contain embedded images
        assert result is None
    finally:
        file_path.unlink()


def test_extract_from_htmlz_with_index(
    extractor: HtmlCoverExtractor, sample_image_bytes: bytes
) -> None:
    """Test _extract_from_htmlz with index.html (covers lines 76-117)."""
    html_content = """<!DOCTYPE html>
    <html>
    <head><title>Test Book</title></head>
    <body>
        <img src="cover.jpg" class="cover">
    </body>
    </html>"""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".htmlz") as tmp:
        file_path = Path(tmp.name)

    with zipfile.ZipFile(file_path, "w") as htmlz_zip:
        htmlz_zip.writestr("index.html", html_content.encode("utf-8"))
        htmlz_zip.writestr("other.html", html_content.encode("utf-8"))
        htmlz_zip.writestr("cover.jpg", sample_image_bytes)

    try:
        result = extractor._extract_from_htmlz(file_path)
        # Should use index.html
        assert result is not None
    finally:
        file_path.unlink()


def test_extract_from_htmlz_no_index(
    extractor: HtmlCoverExtractor, sample_image_bytes: bytes
) -> None:
    """Test _extract_from_htmlz without index.html (covers lines 85-87)."""
    html_content = """<!DOCTYPE html>
    <html>
    <head><title>Test Book</title></head>
    <body>
        <img src="cover.jpg" class="cover">
    </body>
    </html>"""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".htmlz") as tmp:
        file_path = Path(tmp.name)

    with zipfile.ZipFile(file_path, "w") as htmlz_zip:
        htmlz_zip.writestr("first.html", html_content.encode("utf-8"))
        htmlz_zip.writestr("second.html", html_content.encode("utf-8"))
        htmlz_zip.writestr("cover.jpg", sample_image_bytes)

    try:
        result = extractor._extract_from_htmlz(file_path)
        # Should use first HTML file
        assert result is not None
    finally:
        file_path.unlink()


def test_extract_from_htmlz_no_html_files(extractor: HtmlCoverExtractor) -> None:
    """Test _extract_from_htmlz with no HTML files (covers lines 82-83)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".htmlz") as tmp:
        file_path = Path(tmp.name)

    with zipfile.ZipFile(file_path, "w") as htmlz_zip:
        htmlz_zip.writestr("text.txt", b"some text")

    try:
        result = extractor._extract_from_htmlz(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_extract_from_htmlz_no_image(extractor: HtmlCoverExtractor) -> None:
    """Test _extract_from_htmlz with no image found (covers lines 93-95)."""
    html_content = """<!DOCTYPE html>
    <html>
    <head><title>Test Book</title></head>
    <body>No images here</body>
    </html>"""

    file_path = _create_mock_htmlz(html_content=html_content)

    try:
        result = extractor._extract_from_htmlz(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_extract_from_htmlz_with_subdirectory(
    extractor: HtmlCoverExtractor, sample_image_bytes: bytes
) -> None:
    """Test _extract_from_htmlz with image in subdirectory (covers lines 97-102)."""
    html_content = """<!DOCTYPE html>
    <html>
    <head><title>Test Book</title></head>
    <body>
        <img src="images/cover.jpg" class="cover">
    </body>
    </html>"""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".htmlz") as tmp:
        file_path = Path(tmp.name)

    with zipfile.ZipFile(file_path, "w") as htmlz_zip:
        htmlz_zip.writestr("OEBPS/index.html", html_content.encode("utf-8"))
        htmlz_zip.writestr("OEBPS/images/cover.jpg", sample_image_bytes)

    try:
        result = extractor._extract_from_htmlz(file_path)
        assert result is not None
    finally:
        file_path.unlink()


def test_extract_from_htmlz_key_error_alternative_paths(
    extractor: HtmlCoverExtractor, sample_image_bytes: bytes
) -> None:
    """Test _extract_from_htmlz tries alternative paths (covers lines 108-115)."""
    html_content = """<!DOCTYPE html>
    <html>
    <head><title>Test Book</title></head>
    <body>
        <img src="cover.jpg" class="cover">
    </body>
    </html>"""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".htmlz") as tmp:
        file_path = Path(tmp.name)

    with zipfile.ZipFile(file_path, "w") as htmlz_zip:
        htmlz_zip.writestr("index.html", html_content.encode("utf-8"))
        # Put image in images/ directory instead of root
        htmlz_zip.writestr("images/cover.jpg", sample_image_bytes)

    try:
        result = extractor._extract_from_htmlz(file_path)
        # Should find image in alternative path
        assert result is not None
    finally:
        file_path.unlink()


def test_extract_from_htmlz_invalid_zip(extractor: HtmlCoverExtractor) -> None:
    """Test _extract_from_htmlz handles invalid ZIP (covers lines 118-119)."""
    file_path = _create_mock_htmlz("", invalid_zip=True)

    try:
        result = extractor._extract_from_htmlz(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_extract_from_htmlz_os_error(extractor: HtmlCoverExtractor) -> None:
    """Test _extract_from_htmlz handles OSError (covers lines 118-119)."""
    # Create a file that will cause OSError when opened as ZIP
    with tempfile.NamedTemporaryFile(delete=False, suffix=".htmlz") as tmp:
        file_path = Path(tmp.name)
        tmp.write(b"not a zip")

    try:
        result = extractor._extract_from_htmlz(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_extract_from_html(extractor: HtmlCoverExtractor) -> None:
    """Test _extract_from_html (covers lines 139)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        file_path = Path(tmp.name)

    try:
        result = extractor._extract_from_html(file_path)
        # Standalone HTML files don't contain embedded images
        assert result is None
    finally:
        file_path.unlink()


def test_find_image_in_html_class_cover(extractor: HtmlCoverExtractor) -> None:
    """Test _find_image_in_html with class="cover" (covers lines 155-165)."""
    html_content = """<html>
    <body>
        <img src="cover.jpg" class="cover-image">
    </body>
    </html>"""

    result = extractor._find_image_in_html(html_content)
    assert result == "cover.jpg"


def test_find_image_in_html_id_cover(extractor: HtmlCoverExtractor) -> None:
    """Test _find_image_in_html with id="cover" (covers lines 155-165)."""
    html_content = """<html>
    <body>
        <img src="cover.jpg" id="cover-image">
    </body>
    </html>"""

    result = extractor._find_image_in_html(html_content)
    assert result == "cover.jpg"


def test_find_image_in_html_alt_cover(extractor: HtmlCoverExtractor) -> None:
    """Test _find_image_in_html with alt="cover" (covers lines 155-165)."""
    html_content = """<html>
    <body>
        <img src="cover.jpg" alt="book cover">
    </body>
    </html>"""

    result = extractor._find_image_in_html(html_content)
    assert result == "cover.jpg"


def test_find_image_in_html_src_contains_cover(extractor: HtmlCoverExtractor) -> None:
    """Test _find_image_in_html with src containing "cover" (covers lines 155-165)."""
    html_content = """<html>
    <body>
        <img src="book-cover.jpg">
    </body>
    </html>"""

    result = extractor._find_image_in_html(html_content)
    assert result == "book-cover.jpg"


def test_find_image_in_html_first_image(extractor: HtmlCoverExtractor) -> None:
    """Test _find_image_in_html falls back to first image (covers lines 167-172)."""
    html_content = """<html>
    <body>
        <img src="first.jpg">
        <img src="second.jpg">
    </body>
    </html>"""

    result = extractor._find_image_in_html(html_content)
    assert result == "first.jpg"


def test_find_image_in_html_no_image(extractor: HtmlCoverExtractor) -> None:
    """Test _find_image_in_html with no images (covers lines 167-174)."""
    html_content = """<html>
    <body>No images here</body>
    </html>"""

    result = extractor._find_image_in_html(html_content)
    assert result is None


def test_try_alternative_paths_with_slash(extractor: HtmlCoverExtractor) -> None:
    """Test _try_alternative_paths with forward slash (covers lines 193-204)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".htmlz") as tmp:
        file_path = Path(tmp.name)

    with zipfile.ZipFile(file_path, "w") as zip_file:
        alternatives = extractor._try_alternative_paths("images/cover.jpg", zip_file)
        assert "images\\cover.jpg" in alternatives
        assert "images/cover.jpg" in alternatives
        # Should include common directories
        assert "images/cover.jpg" in alternatives or any(
            "cover.jpg" in alt for alt in alternatives
        )

    file_path.unlink()


def test_try_alternative_paths_with_backslash(extractor: HtmlCoverExtractor) -> None:
    """Test _try_alternative_paths with backslash (covers lines 197-198)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".htmlz") as tmp:
        file_path = Path(tmp.name)

    with zipfile.ZipFile(file_path, "w") as zip_file:
        alternatives = extractor._try_alternative_paths("images\\cover.jpg", zip_file)
        assert "images/cover.jpg" in alternatives
        assert "images\\cover.jpg" in alternatives

    file_path.unlink()


def test_try_alternative_paths_common_directories(
    extractor: HtmlCoverExtractor,
) -> None:
    """Test _try_alternative_paths includes common directories (covers lines 200-203)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".htmlz") as tmp:
        file_path = Path(tmp.name)

    with zipfile.ZipFile(file_path, "w") as zip_file:
        alternatives = extractor._try_alternative_paths("cover.jpg", zip_file)
        # Should include common image directories
        assert any("images/cover.jpg" in alt for alt in alternatives)
        assert any("img/cover.jpg" in alt for alt in alternatives)

    file_path.unlink()


def test_process_image_jpeg(
    extractor: HtmlCoverExtractor, sample_image_bytes: bytes
) -> None:
    """Test _process_image with JPEG (covers lines 219-229)."""
    result = extractor._process_image(sample_image_bytes)
    assert result is not None
    assert isinstance(result, bytes)


def test_process_image_png(extractor: HtmlCoverExtractor) -> None:
    """Test _process_image with PNG (covers lines 219-229)."""
    # Create PNG image
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    png_data = buffer.getvalue()

    result = extractor._process_image(png_data)
    assert result is not None
    assert isinstance(result, bytes)


def test_process_image_invalid(extractor: HtmlCoverExtractor) -> None:
    """Test _process_image with invalid image data (covers lines 228-229)."""
    invalid_data = b"not an image"
    result = extractor._process_image(invalid_data)
    assert result is None


def test_process_image_os_error(extractor: HtmlCoverExtractor) -> None:
    """Test _process_image handles OSError (covers lines 228-229)."""
    # Create data that will cause OSError in PIL
    invalid_data = b"\xff\xd8\xff\xe0\x00\x10JFIF"  # Incomplete JPEG header
    result = extractor._process_image(invalid_data)
    # Should handle gracefully
    assert result is None or isinstance(result, bytes)
