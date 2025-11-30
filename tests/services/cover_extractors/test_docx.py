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

"""Tests for DocxCoverExtractor."""

from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image  # type: ignore[import-untyped]

from fundamental.services.cover_extractors.docx import DocxCoverExtractor


@pytest.fixture
def extractor() -> DocxCoverExtractor:
    """Create DocxCoverExtractor instance for testing.

    Returns
    -------
    DocxCoverExtractor
        Extractor instance.
    """
    return DocxCoverExtractor()


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Create sample image bytes for testing.

    Returns
    -------
    bytes
        JPEG image data as bytes.
    """
    img = Image.new("RGB", (100, 100), color="blue")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def sample_png_bytes() -> bytes:
    """Create sample PNG image bytes for testing.

    Returns
    -------
    bytes
        PNG image data as bytes.
    """
    img = Image.new("RGBA", (100, 100), color=(0, 0, 255, 128))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def docx_file_with_images(sample_image_bytes: bytes, tmp_path: Path) -> Path:
    """Create a DOCX file with images in word/media/ for testing.

    Parameters
    ----------
    sample_image_bytes : bytes
        Image data to include.
    tmp_path : Path
        Temporary directory path.

    Returns
    -------
    Path
        Path to created DOCX file.
    """
    import zipfile

    docx_path = tmp_path / "test.docx"
    with zipfile.ZipFile(docx_path, "w") as docx_zip:
        docx_zip.writestr("word/media/image1.jpg", sample_image_bytes)
        docx_zip.writestr("word/media/image2.png", sample_image_bytes)
        docx_zip.writestr("word/document.xml", b"<xml>content</xml>")
        docx_zip.writestr("[Content_Types].xml", b"<xml>types</xml>")
    return docx_path


@pytest.fixture
def docx_file_no_images(tmp_path: Path) -> Path:
    """Create a DOCX file without images for testing.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory path.

    Returns
    -------
    Path
        Path to created DOCX file.
    """
    import zipfile

    docx_path = tmp_path / "test_no_images.docx"
    with zipfile.ZipFile(docx_path, "w") as docx_zip:
        docx_zip.writestr("word/document.xml", b"<xml>content</xml>")
        docx_zip.writestr("[Content_Types].xml", b"<xml>types</xml>")
    return docx_path


@pytest.mark.parametrize(
    ("file_format", "expected"),
    [
        ("DOCX", True),
        ("docx", True),
        (".DOCX", True),
        (".docx", True),
        ("EPUB", False),
        ("PDF", False),
        ("", False),
    ],
)
def test_can_handle(
    extractor: DocxCoverExtractor, file_format: str, expected: bool
) -> None:
    """Test can_handle returns correct result for various formats.

    Parameters
    ----------
    extractor : DocxCoverExtractor
        Extractor instance.
    file_format : str
        File format to test.
    expected : bool
        Expected result.
    """
    assert extractor.can_handle(file_format) == expected


def test_extract_cover_success(
    extractor: DocxCoverExtractor,
    docx_file_with_images: Path,
    sample_image_bytes: bytes,
) -> None:
    """Test extract_cover successfully extracts cover from DOCX.

    Parameters
    ----------
    extractor : DocxCoverExtractor
        Extractor instance.
    docx_file_with_images : Path
        DOCX file with images.
    sample_image_bytes : bytes
        Expected image bytes.
    """
    result = extractor.extract_cover(docx_file_with_images)
    assert result is not None
    assert isinstance(result, bytes)
    # Should be JPEG (processed)
    assert len(result) > 0


def test_extract_cover_no_images(
    extractor: DocxCoverExtractor, docx_file_no_images: Path
) -> None:
    """Test extract_cover returns None when no images found.

    Parameters
    ----------
    extractor : DocxCoverExtractor
        Extractor instance.
    docx_file_no_images : Path
        DOCX file without images.
    """
    result = extractor.extract_cover(docx_file_no_images)
    assert result is None


def test_extract_cover_bad_zip(extractor: DocxCoverExtractor, tmp_path: Path) -> None:
    """Test extract_cover handles bad ZIP file gracefully.

    Parameters
    ----------
    extractor : DocxCoverExtractor
        Extractor instance.
    tmp_path : Path
        Temporary directory path.
    """
    bad_zip = tmp_path / "bad.docx"
    bad_zip.write_text("not a zip file")
    result = extractor.extract_cover(bad_zip)
    assert result is None


def test_extract_cover_missing_file(
    extractor: DocxCoverExtractor, tmp_path: Path
) -> None:
    """Test extract_cover handles missing file gracefully.

    Parameters
    ----------
    extractor : DocxCoverExtractor
        Extractor instance.
    tmp_path : Path
        Temporary directory path.
    """
    missing_file = tmp_path / "nonexistent.docx"
    result = extractor.extract_cover(missing_file)
    assert result is None


@pytest.mark.parametrize(
    "image_ext",
    [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
)
def test_extract_cover_various_formats(
    extractor: DocxCoverExtractor,
    sample_image_bytes: bytes,
    sample_png_bytes: bytes,
    tmp_path: Path,
    image_ext: str,
) -> None:
    """Test extract_cover handles various image formats.

    Parameters
    ----------
    extractor : DocxCoverExtractor
        Extractor instance.
    sample_image_bytes : bytes
        JPEG image bytes.
    sample_png_bytes : bytes
        PNG image bytes.
    tmp_path : Path
        Temporary directory path.
    image_ext : str
        Image extension to test.
    """
    import zipfile

    docx_path = tmp_path / f"test{image_ext}.docx"
    image_data = sample_png_bytes if image_ext == ".png" else sample_image_bytes
    with zipfile.ZipFile(docx_path, "w") as docx_zip:
        docx_zip.writestr(f"word/media/cover{image_ext}", image_data)
        docx_zip.writestr("word/document.xml", b"<xml>content</xml>")

    result = extractor.extract_cover(docx_path)
    assert result is not None
    assert isinstance(result, bytes)


def test_extract_cover_key_error(
    extractor: DocxCoverExtractor, sample_image_bytes: bytes, tmp_path: Path
) -> None:
    """Test extract_cover handles KeyError gracefully.

    Parameters
    ----------
    extractor : DocxCoverExtractor
        Extractor instance.
    sample_image_bytes : bytes
        Image data to include.
    tmp_path : Path
        Temporary directory path.
    """
    import zipfile

    docx_path = tmp_path / "test.docx"
    with zipfile.ZipFile(docx_path, "w") as docx_zip:
        docx_zip.writestr("word/media/image1.jpg", sample_image_bytes)

    # Mock read to raise KeyError
    with patch("zipfile.ZipFile.read", side_effect=KeyError("File not found")):
        result = extractor.extract_cover(docx_path)
        assert result is None


def test_process_image_success(
    extractor: DocxCoverExtractor, sample_image_bytes: bytes
) -> None:
    """Test _process_image successfully converts image to JPEG.

    Parameters
    ----------
    extractor : DocxCoverExtractor
        Extractor instance.
    sample_image_bytes : bytes
        Image data to process.
    """
    result = extractor._process_image(sample_image_bytes)
    assert result is not None
    assert isinstance(result, bytes)
    # Verify it's valid JPEG
    img = Image.open(BytesIO(result))
    assert img.format == "JPEG"
    assert img.mode == "RGB"


def test_process_image_png_to_jpeg(
    extractor: DocxCoverExtractor, sample_png_bytes: bytes
) -> None:
    """Test _process_image converts PNG to JPEG.

    Parameters
    ----------
    extractor : DocxCoverExtractor
        Extractor instance.
    sample_png_bytes : bytes
        PNG image data to process.
    """
    result = extractor._process_image(sample_png_bytes)
    assert result is not None
    assert isinstance(result, bytes)
    # Verify it's valid JPEG (converted from PNG)
    img = Image.open(BytesIO(result))
    assert img.format == "JPEG"
    assert img.mode == "RGB"


def test_process_image_rgb_mode(extractor: DocxCoverExtractor, tmp_path: Path) -> None:
    """Test _process_image handles RGB mode images correctly.

    Parameters
    ----------
    extractor : DocxCoverExtractor
        Extractor instance.
    tmp_path : Path
        Temporary directory path.
    """
    # Create RGB image
    img = Image.new("RGB", (50, 50), color="green")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    rgb_bytes = buffer.getvalue()

    result = extractor._process_image(rgb_bytes)
    assert result is not None
    assert isinstance(result, bytes)


def test_process_image_invalid_data(extractor: DocxCoverExtractor) -> None:
    """Test _process_image handles invalid image data gracefully.

    Parameters
    ----------
    extractor : DocxCoverExtractor
        Extractor instance.
    """
    invalid_data = b"not an image"
    result = extractor._process_image(invalid_data)
    assert result is None


def test_process_image_empty_data(extractor: DocxCoverExtractor) -> None:
    """Test _process_image handles empty data gracefully.

    Parameters
    ----------
    extractor : DocxCoverExtractor
        Extractor instance.
    """
    result = extractor._process_image(b"")
    assert result is None


def test_extract_cover_images_outside_media_folder(
    extractor: DocxCoverExtractor, sample_image_bytes: bytes, tmp_path: Path
) -> None:
    """Test extract_cover only finds images in word/media/ folder.

    Parameters
    ----------
    extractor : DocxCoverExtractor
        Extractor instance.
    sample_image_bytes : bytes
        Image data to include.
    tmp_path : Path
        Temporary directory path.
    """
    import zipfile

    docx_path = tmp_path / "test.docx"
    with zipfile.ZipFile(docx_path, "w") as docx_zip:
        # Image outside media folder should be ignored
        docx_zip.writestr("image.jpg", sample_image_bytes)
        docx_zip.writestr("word/document.xml", b"<xml>content</xml>")

    result = extractor.extract_cover(docx_path)
    assert result is None


def test_extract_cover_multiple_images_uses_first(
    extractor: DocxCoverExtractor, sample_image_bytes: bytes, tmp_path: Path
) -> None:
    """Test extract_cover uses first image when multiple images exist.

    Parameters
    ----------
    extractor : DocxCoverExtractor
        Extractor instance.
    sample_image_bytes : bytes
        Image data to include.
    tmp_path : Path
        Temporary directory path.
    """
    import zipfile

    docx_path = tmp_path / "test.docx"
    with zipfile.ZipFile(docx_path, "w") as docx_zip:
        docx_zip.writestr("word/media/image1.jpg", sample_image_bytes)
        docx_zip.writestr("word/media/image2.png", sample_image_bytes)
        docx_zip.writestr("word/media/image3.gif", sample_image_bytes)
        docx_zip.writestr("word/document.xml", b"<xml>content</xml>")

    result = extractor.extract_cover(docx_path)
    assert result is not None
    assert isinstance(result, bytes)
