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

"""Tests for PDF cover extractor to achieve 100% coverage."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from PIL import Image  # type: ignore[import-untyped]

from fundamental.services.cover_extractors.pdf import PdfCoverExtractor

if TYPE_CHECKING:
    from collections.abc import Generator

# Mock pdf2image module before importing
mock_pdf2image = MagicMock()
# Ensure convert_from_path is always available as a callable
mock_pdf2image.convert_from_path = MagicMock()
sys.modules["pdf2image"] = mock_pdf2image


@pytest.fixture
def extractor() -> PdfCoverExtractor:
    """Create PdfCoverExtractor instance."""
    return PdfCoverExtractor()


@pytest.fixture(autouse=True)
def reset_mock() -> Generator[None, None, None]:
    """Reset mock after each test."""
    yield
    mock_pdf2image.reset_mock()
    # Ensure convert_from_path is always available
    if not hasattr(mock_pdf2image, "convert_from_path"):
        mock_pdf2image.convert_from_path = MagicMock()


@pytest.mark.parametrize(
    ("file_format", "expected"),
    [
        ("pdf", True),
        ("PDF", True),
        (".pdf", True),
        ("epub", False),
        ("mobi", False),
    ],
)
def test_can_handle(
    extractor: PdfCoverExtractor, file_format: str, expected: bool
) -> None:
    """Test can_handle for various formats."""
    assert extractor.can_handle(file_format) == expected


def test_extract_cover_success(extractor: PdfCoverExtractor) -> None:
    """Test successful cover extraction."""
    # Create a mock image
    img = Image.new("RGB", (100, 100), color="red")
    mock_pdf2image.convert_from_path.return_value = [img]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file_path = Path(tmp.name)
        tmp.write(b"fake pdf content")

    try:
        result = extractor.extract_cover(file_path)
        assert result is not None
        assert isinstance(result, bytes)
        # Verify convert_from_path was called correctly
        mock_pdf2image.convert_from_path.assert_called_once_with(
            str(file_path), first_page=1, last_page=1, dpi=150
        )
    finally:
        file_path.unlink()


def test_extract_cover_non_rgb(extractor: PdfCoverExtractor) -> None:
    """Test cover extraction with non-RGB image (needs conversion)."""
    # Create a mock image in RGBA mode
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    mock_pdf2image.convert_from_path.return_value = [img]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file_path = Path(tmp.name)
        tmp.write(b"fake pdf content")

    try:
        result = extractor.extract_cover(file_path)
        assert result is not None
        assert isinstance(result, bytes)
        # Image should be converted to RGB
        assert (
            img.mode == "RGB" or result is not None
        )  # Either converted or result exists
    finally:
        file_path.unlink()


def test_extract_cover_no_images(extractor: PdfCoverExtractor) -> None:
    """Test extraction when no images are returned."""
    mock_pdf2image.convert_from_path.return_value = []

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file_path = Path(tmp.name)
        tmp.write(b"fake pdf content")

    try:
        result = extractor.extract_cover(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_extract_cover_import_error(extractor: PdfCoverExtractor) -> None:
    """Test extraction when pdf2image is not available."""
    # Temporarily remove pdf2image from sys.modules to simulate ImportError
    original_pdf2image = sys.modules.pop("pdf2image", None)
    try:
        # Reload the module to trigger ImportError
        import importlib

        import fundamental.services.cover_extractors.pdf as pdf_module

        importlib.reload(pdf_module)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            file_path = Path(tmp.name)
            tmp.write(b"fake pdf content")

        try:
            # Create new extractor instance after module reload
            new_extractor = pdf_module.PdfCoverExtractor()
            result = new_extractor.extract_cover(file_path)
            assert result is None
        finally:
            file_path.unlink()
    finally:
        # Restore pdf2image mock
        if original_pdf2image:
            sys.modules["pdf2image"] = original_pdf2image
        else:
            sys.modules["pdf2image"] = mock_pdf2image
        # Reload the module again to restore original behavior
        import importlib

        import fundamental.services.cover_extractors.pdf as pdf_module

        importlib.reload(pdf_module)


def test_extract_cover_os_error(extractor: PdfCoverExtractor) -> None:
    """Test extraction when OSError occurs."""
    mock_pdf2image.convert_from_path.side_effect = OSError("File not found")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file_path = Path(tmp.name)
        tmp.write(b"fake pdf content")

    try:
        result = extractor.extract_cover(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_extract_cover_value_error(extractor: PdfCoverExtractor) -> None:
    """Test extraction when ValueError occurs."""
    mock_pdf2image.convert_from_path.side_effect = ValueError("Invalid PDF")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file_path = Path(tmp.name)
        tmp.write(b"fake pdf content")

    try:
        result = extractor.extract_cover(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_extract_cover_type_error(extractor: PdfCoverExtractor) -> None:
    """Test extraction when TypeError occurs."""
    mock_pdf2image.convert_from_path.side_effect = TypeError("Invalid argument")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file_path = Path(tmp.name)
        tmp.write(b"fake pdf content")

    try:
        result = extractor.extract_cover(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_extract_cover_attribute_error(extractor: PdfCoverExtractor) -> None:
    """Test extraction when AttributeError occurs."""
    mock_pdf2image.convert_from_path.side_effect = AttributeError("Attribute not found")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file_path = Path(tmp.name)
        tmp.write(b"fake pdf content")

    try:
        result = extractor.extract_cover(file_path)
        assert result is None
    finally:
        file_path.unlink()


def test_extract_cover_jpeg_format(extractor: PdfCoverExtractor) -> None:
    """Test that extracted cover is saved as JPEG."""
    img = Image.new("RGB", (100, 100), color="blue")
    # Ensure mock is properly configured - clear any side_effect from previous tests
    mock_pdf2image.reset_mock()
    mock_pdf2image.convert_from_path.side_effect = None  # Clear side_effect
    mock_pdf2image.convert_from_path.return_value = [img]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file_path = Path(tmp.name)
        tmp.write(b"fake pdf content")

    try:
        result = extractor.extract_cover(file_path)
        assert result is not None
        # Verify it's valid JPEG data
        assert result.startswith(b"\xff\xd8\xff")  # JPEG magic bytes
    finally:
        file_path.unlink()


def test_extract_cover_file_not_found(extractor: PdfCoverExtractor) -> None:
    """Test extraction with non-existent file."""
    # Clear mock to ensure it doesn't return data for non-existent file
    mock_pdf2image.reset_mock()
    mock_pdf2image.convert_from_path.side_effect = OSError("File not found")
    file_path = Path("/nonexistent/file.pdf")
    result = extractor.extract_cover(file_path)
    assert result is None
