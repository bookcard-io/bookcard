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

"""Tests for CbzCoverExtractor."""

import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image  # type: ignore[import-untyped]

from bookcard.services.cover_extractors.cbz import CbzCoverExtractor


@pytest.fixture
def extractor() -> CbzCoverExtractor:
    """Create CbzCoverExtractor instance for testing.

    Returns
    -------
    CbzCoverExtractor
        Extractor instance.
    """
    return CbzCoverExtractor()


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


@pytest.fixture
def sample_png_bytes() -> bytes:
    """Create sample PNG image bytes for testing.

    Returns
    -------
    bytes
        PNG image data as bytes.
    """
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def cbz_file_with_images(sample_image_bytes: bytes, tmp_path: Path) -> Path:
    """Create a CBZ file with images for testing.

    Parameters
    ----------
    sample_image_bytes : bytes
        Image data to include.
    tmp_path : Path
        Temporary directory path.

    Returns
    -------
    Path
        Path to created CBZ file.
    """
    import zipfile

    cbz_path = tmp_path / "test.cbz"
    with zipfile.ZipFile(cbz_path, "w") as cbz_zip:
        cbz_zip.writestr("page01.jpg", sample_image_bytes)
        cbz_zip.writestr("page02.jpg", sample_image_bytes)
        cbz_zip.writestr("metadata.txt", b"Some metadata")
    return cbz_path


@pytest.fixture
def cbz_file_no_images(tmp_path: Path) -> Path:
    """Create a CBZ file without images for testing.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory path.

    Returns
    -------
    Path
        Path to created CBZ file.
    """
    import zipfile

    cbz_path = tmp_path / "test_no_images.cbz"
    with zipfile.ZipFile(cbz_path, "w") as cbz_zip:
        cbz_zip.writestr("metadata.txt", b"Some metadata")
        cbz_zip.writestr("readme.txt", b"Readme")
    return cbz_path


@pytest.fixture
def cbc_file_with_cbz(cbz_file_with_images: Path, tmp_path: Path) -> Path:
    """Create a CBC file containing a CBZ for testing.

    Parameters
    ----------
    cbz_file_with_images : Path
        CBZ file to include in collection.
    tmp_path : Path
        Temporary directory path.

    Returns
    -------
    Path
        Path to created CBC file.
    """
    import zipfile

    cbc_path = tmp_path / "test.cbc"
    with zipfile.ZipFile(cbc_path, "w") as cbc_zip:
        cbc_zip.write(cbz_file_with_images, "book1.cbz")
    return cbc_path


@pytest.mark.parametrize(
    ("file_format", "expected"),
    [
        ("CBZ", True),
        ("CBR", True),
        ("CB7", True),
        ("CBC", True),
        ("cbz", True),
        ("cbr", True),
        ("cb7", True),
        ("cbc", True),
        (".CBZ", True),
        (".CBR", True),
        ("EPUB", False),
        ("PDF", False),
        ("", False),
    ],
)
def test_can_handle(
    extractor: CbzCoverExtractor, file_format: str, expected: bool
) -> None:
    """Test can_handle returns correct result for various formats.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    file_format : str
        File format to test.
    expected : bool
        Expected result.
    """
    assert extractor.can_handle(file_format) == expected


def test_extract_cover_unsupported_format(
    extractor: CbzCoverExtractor, tmp_path: Path
) -> None:
    """Test extract_cover returns None for unsupported format.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    tmp_path : Path
        Temporary directory path.
    """
    file_path = tmp_path / "test.unknown"
    file_path.touch()
    result = extractor.extract_cover(file_path)
    assert result is None


def test_extract_from_cbz_success(
    extractor: CbzCoverExtractor,
    cbz_file_with_images: Path,
    sample_image_bytes: bytes,
) -> None:
    """Test _extract_from_cbz successfully extracts cover from CBZ.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    cbz_file_with_images : Path
        CBZ file with images.
    sample_image_bytes : bytes
        Expected image bytes.
    """
    result = extractor._extract_from_cbz(cbz_file_with_images)
    assert result is not None
    assert isinstance(result, bytes)
    # Should be JPEG (processed)
    assert len(result) > 0


def test_extract_from_cbz_no_images(
    extractor: CbzCoverExtractor, cbz_file_no_images: Path
) -> None:
    """Test _extract_from_cbz returns None when no images found.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    cbz_file_no_images : Path
        CBZ file without images.
    """
    result = extractor._extract_from_cbz(cbz_file_no_images)
    assert result is None


def test_extract_from_cbz_bad_zip(extractor: CbzCoverExtractor, tmp_path: Path) -> None:
    """Test _extract_from_cbz handles bad ZIP file gracefully.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    tmp_path : Path
        Temporary directory path.
    """
    bad_zip = tmp_path / "bad.cbz"
    bad_zip.write_text("not a zip file")
    result = extractor._extract_from_cbz(bad_zip)
    assert result is None


def test_extract_from_cbz_missing_file(
    extractor: CbzCoverExtractor, tmp_path: Path
) -> None:
    """Test _extract_from_cbz handles missing file gracefully.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    tmp_path : Path
        Temporary directory path.
    """
    missing_file = tmp_path / "nonexistent.cbz"
    result = extractor._extract_from_cbz(missing_file)
    assert result is None


@pytest.mark.parametrize(
    "image_ext",
    [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
)
def test_extract_from_cbz_various_formats(
    extractor: CbzCoverExtractor,
    sample_image_bytes: bytes,
    sample_png_bytes: bytes,
    tmp_path: Path,
    image_ext: str,
) -> None:
    """Test _extract_from_cbz handles various image formats.

    Parameters
    ----------
    extractor : CbzCoverExtractor
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

    cbz_path = tmp_path / f"test{image_ext}.cbz"
    image_data = sample_png_bytes if image_ext == ".png" else sample_image_bytes
    with zipfile.ZipFile(cbz_path, "w") as cbz_zip:
        cbz_zip.writestr(f"cover{image_ext}", image_data)

    result = extractor._extract_from_cbz(cbz_path)
    assert result is not None
    assert isinstance(result, bytes)


def test_extract_from_cbr_with_rarfile(
    extractor: CbzCoverExtractor, sample_image_bytes: bytes, tmp_path: Path
) -> None:
    """Test _extract_from_cbr when rarfile is available.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    sample_image_bytes : bytes
        Image data to include.
    tmp_path : Path
        Temporary directory path.
    """
    cbr_path = tmp_path / "test.cbr"
    # Mock rarfile module in sys.modules before import
    mock_rarfile = MagicMock()
    mock_rar_file = MagicMock()
    mock_rar_file.__enter__ = MagicMock(return_value=mock_rar_file)
    mock_rar_file.__exit__ = MagicMock(return_value=None)
    mock_rar_file.namelist.return_value = ["page01.jpg", "page02.jpg"]
    mock_rar_file.read.return_value = sample_image_bytes
    mock_rarfile.RarFile.return_value = mock_rar_file

    # Inject mock into sys.modules
    original_rarfile = sys.modules.get("rarfile")
    sys.modules["rarfile"] = mock_rarfile  # type: ignore[assignment]

    try:
        result = extractor._extract_from_cbr(cbr_path)
        assert result is not None
        assert isinstance(result, bytes)
    finally:
        # Restore original module
        if original_rarfile is not None:
            sys.modules["rarfile"] = original_rarfile
        elif "rarfile" in sys.modules:
            del sys.modules["rarfile"]


def test_extract_from_cbr_without_rarfile(
    extractor: CbzCoverExtractor, tmp_path: Path
) -> None:
    """Test _extract_from_cbr when rarfile is not available.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    tmp_path : Path
        Temporary directory path.
    """
    cbr_path = tmp_path / "test.cbr"
    # Remove rarfile from sys.modules to simulate ImportError
    original_rarfile = sys.modules.pop("rarfile", None)
    try:
        result = extractor._extract_from_cbr(cbr_path)
        assert result is None
    finally:
        if original_rarfile is not None:
            sys.modules["rarfile"] = original_rarfile


def test_extract_from_cbr_no_images(
    extractor: CbzCoverExtractor, tmp_path: Path
) -> None:
    """Test _extract_from_cbr returns None when no images found.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    tmp_path : Path
        Temporary directory path.
    """
    cbr_path = tmp_path / "test.cbr"
    # Mock rarfile module with no images
    mock_rarfile = MagicMock()
    mock_rar_file = MagicMock()
    mock_rar_file.__enter__ = MagicMock(return_value=mock_rar_file)
    mock_rar_file.__exit__ = MagicMock(return_value=None)
    mock_rar_file.namelist.return_value = ["readme.txt", "metadata.txt"]  # No images
    mock_rarfile.RarFile.return_value = mock_rar_file

    # Inject mock into sys.modules
    original_rarfile = sys.modules.get("rarfile")
    sys.modules["rarfile"] = mock_rarfile  # type: ignore[assignment]

    try:
        result = extractor._extract_from_cbr(cbr_path)
        assert result is None
    finally:
        # Restore original module
        if original_rarfile is not None:
            sys.modules["rarfile"] = original_rarfile
        elif "rarfile" in sys.modules:
            del sys.modules["rarfile"]


def test_extract_from_cbr_rarfile_error(
    extractor: CbzCoverExtractor, sample_image_bytes: bytes, tmp_path: Path
) -> None:
    """Test _extract_from_cbr handles rarfile errors gracefully.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    sample_image_bytes : bytes
        Image data to include.
    tmp_path : Path
        Temporary directory path.
    """
    cbr_path = tmp_path / "test.cbr"
    # Mock rarfile module with error
    mock_rarfile = MagicMock()
    mock_rar_file = MagicMock()
    mock_rar_file.__enter__ = MagicMock(return_value=mock_rar_file)
    mock_rar_file.__exit__ = MagicMock(return_value=None)
    # Create a mock Error class
    mock_rarfile.Error = type("Error", (Exception,), {})
    mock_rar_file.namelist.side_effect = mock_rarfile.Error("RAR error")
    mock_rarfile.RarFile.return_value = mock_rar_file

    # Inject mock into sys.modules
    original_rarfile = sys.modules.get("rarfile")
    sys.modules["rarfile"] = mock_rarfile  # type: ignore[assignment]

    try:
        result = extractor._extract_from_cbr(cbr_path)
        assert result is None
    finally:
        # Restore original module
        if original_rarfile is not None:
            sys.modules["rarfile"] = original_rarfile
        elif "rarfile" in sys.modules:
            del sys.modules["rarfile"]


def test_extract_from_cb7_with_py7zr(
    extractor: CbzCoverExtractor, sample_image_bytes: bytes, tmp_path: Path
) -> None:
    """Test _extract_from_cb7 when py7zr is available.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    sample_image_bytes : bytes
        Image data to include.
    tmp_path : Path
        Temporary directory path.
    """
    cb7_path = tmp_path / "test.cb7"
    # Mock py7zr module in sys.modules before import
    mock_py7zr = MagicMock()
    mock_7z_file = MagicMock()
    mock_7z_file.__enter__ = MagicMock(return_value=mock_7z_file)
    mock_7z_file.__exit__ = MagicMock(return_value=None)
    mock_7z_file.getnames.return_value = ["page01.jpg", "page02.jpg"]
    mock_file_obj = MagicMock()
    mock_file_obj.read.return_value = sample_image_bytes
    mock_7z_file.read.return_value = {"page01.jpg": mock_file_obj}
    mock_py7zr.SevenZipFile.return_value = mock_7z_file

    # Inject mock into sys.modules
    original_py7zr = sys.modules.get("py7zr")
    sys.modules["py7zr"] = mock_py7zr  # type: ignore[assignment]

    try:
        result = extractor._extract_from_cb7(cb7_path)
        assert result is not None
        assert isinstance(result, bytes)
    finally:
        # Restore original module
        if original_py7zr is not None:
            sys.modules["py7zr"] = original_py7zr
        elif "py7zr" in sys.modules:
            del sys.modules["py7zr"]


def test_extract_from_cb7_without_py7zr(
    extractor: CbzCoverExtractor, tmp_path: Path
) -> None:
    """Test _extract_from_cb7 when py7zr is not available.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    tmp_path : Path
        Temporary directory path.
    """
    import builtins

    cb7_path = tmp_path / "test.cb7"
    # Remove py7zr from sys.modules and mock __import__ to raise ImportError
    original_py7zr = sys.modules.pop("py7zr", None)
    original_import = builtins.__import__

    def import_with_error(
        name: str,
        globals: object | None = None,  # noqa: A002
        locals: object | None = None,  # noqa: A002
        fromlist: object = (),
        level: int = 0,
    ) -> object:
        """Mock import that raises ImportError for py7zr."""
        if name == "py7zr":
            raise ImportError("No module named 'py7zr'")
        # Type ignore needed because __import__ signature is complex
        return original_import(name, globals, locals, fromlist, level)  # type: ignore[arg-type]

    try:
        # Patch __import__ to raise ImportError for py7zr
        builtins.__import__ = import_with_error  # type: ignore[assignment]
        result = extractor._extract_from_cb7(cb7_path)
        assert result is None
    finally:
        builtins.__import__ = original_import
        if original_py7zr is not None:
            sys.modules["py7zr"] = original_py7zr


def test_extract_from_cb7_no_images(
    extractor: CbzCoverExtractor, tmp_path: Path
) -> None:
    """Test _extract_from_cb7 returns None when no images found.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    tmp_path : Path
        Temporary directory path.
    """
    cb7_path = tmp_path / "test.cb7"
    # Mock py7zr module with no images
    mock_py7zr = MagicMock()
    mock_7z_file = MagicMock()
    mock_7z_file.__enter__ = MagicMock(return_value=mock_7z_file)
    mock_7z_file.__exit__ = MagicMock(return_value=None)
    mock_7z_file.getnames.return_value = ["readme.txt", "metadata.txt"]  # No images
    mock_py7zr.SevenZipFile.return_value = mock_7z_file

    # Inject mock into sys.modules
    original_py7zr = sys.modules.get("py7zr")
    sys.modules["py7zr"] = mock_py7zr  # type: ignore[assignment]

    try:
        result = extractor._extract_from_cb7(cb7_path)
        assert result is None
    finally:
        # Restore original module
        if original_py7zr is not None:
            sys.modules["py7zr"] = original_py7zr
        elif "py7zr" in sys.modules:
            del sys.modules["py7zr"]


def test_extract_from_cb7_py7zr_error(
    extractor: CbzCoverExtractor, sample_image_bytes: bytes, tmp_path: Path
) -> None:
    """Test _extract_from_cb7 handles py7zr errors gracefully.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    sample_image_bytes : bytes
        Image data to include.
    tmp_path : Path
        Temporary directory path.
    """
    cb7_path = tmp_path / "test.cb7"
    # Mock py7zr module with error
    mock_py7zr = MagicMock()
    mock_7z_file = MagicMock()
    mock_7z_file.__enter__ = MagicMock(return_value=mock_7z_file)
    mock_7z_file.__exit__ = MagicMock(return_value=None)
    mock_7z_file.getnames.side_effect = OSError("7z error")
    mock_py7zr.SevenZipFile.return_value = mock_7z_file

    # Inject mock into sys.modules
    original_py7zr = sys.modules.get("py7zr")
    sys.modules["py7zr"] = mock_py7zr  # type: ignore[assignment]

    try:
        result = extractor._extract_from_cb7(cb7_path)
        assert result is None
    finally:
        # Restore original module
        if original_py7zr is not None:
            sys.modules["py7zr"] = original_py7zr
        elif "py7zr" in sys.modules:
            del sys.modules["py7zr"]


def test_extract_from_cbc_success(
    extractor: CbzCoverExtractor,
    cbc_file_with_cbz: Path,
    sample_image_bytes: bytes,
) -> None:
    """Test _extract_from_cbc successfully extracts cover from CBC.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    cbc_file_with_cbz : Path
        CBC file containing CBZ.
    sample_image_bytes : bytes
        Expected image bytes.
    """
    result = extractor._extract_from_cbc(cbc_file_with_cbz)
    assert result is not None
    assert isinstance(result, bytes)


def test_extract_from_cbc_no_cbz_files(
    extractor: CbzCoverExtractor, cbz_file_no_images: Path, tmp_path: Path
) -> None:
    """Test _extract_from_cbc returns None when no CBZ files found.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    cbz_file_no_images : Path
        CBZ file without images (used to create CBC).
    tmp_path : Path
        Temporary directory path.
    """
    import zipfile

    cbc_path = tmp_path / "test_no_cbz.cbc"
    with zipfile.ZipFile(cbc_path, "w") as cbc_zip:
        cbc_zip.writestr("readme.txt", b"Readme")
        cbc_zip.writestr("metadata.txt", b"Metadata")

    result = extractor._extract_from_cbc(cbc_path)
    assert result is None


def test_extract_from_cbc_bad_zip(extractor: CbzCoverExtractor, tmp_path: Path) -> None:
    """Test _extract_from_cbc handles bad ZIP file gracefully.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    tmp_path : Path
        Temporary directory path.
    """
    bad_zip = tmp_path / "bad.cbc"
    bad_zip.write_text("not a zip file")
    result = extractor._extract_from_cbc(bad_zip)
    assert result is None


def test_extract_from_cbc_key_error(
    extractor: CbzCoverExtractor, cbz_file_with_images: Path, tmp_path: Path
) -> None:
    """Test _extract_from_cbc handles KeyError gracefully.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    cbz_file_with_images : Path
        CBZ file with images.
    tmp_path : Path
        Temporary directory path.
    """
    import zipfile

    cbc_path = tmp_path / "test.cbc"
    with zipfile.ZipFile(cbc_path, "w") as cbc_zip:
        # Add a CBZ entry but make it inaccessible
        cbc_zip.writestr("book1.cbz", b"fake cbz data")

    # Mock the read to raise KeyError
    with patch("zipfile.ZipFile.read", side_effect=KeyError("File not found")):
        result = extractor._extract_from_cbc(cbc_path)
        assert result is None


def test_process_image_success(
    extractor: CbzCoverExtractor, sample_image_bytes: bytes
) -> None:
    """Test _process_image successfully converts image to JPEG.

    Parameters
    ----------
    extractor : CbzCoverExtractor
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
    extractor: CbzCoverExtractor, sample_png_bytes: bytes
) -> None:
    """Test _process_image converts PNG to JPEG.

    Parameters
    ----------
    extractor : CbzCoverExtractor
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


def test_process_image_invalid_data(extractor: CbzCoverExtractor) -> None:
    """Test _process_image handles invalid image data gracefully.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    """
    invalid_data = b"not an image"
    result = extractor._process_image(invalid_data)
    assert result is None


def test_process_image_empty_data(extractor: CbzCoverExtractor) -> None:
    """Test _process_image handles empty data gracefully.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    """
    result = extractor._process_image(b"")
    assert result is None


def test_extract_cover_cbz_integration(
    extractor: CbzCoverExtractor,
    cbz_file_with_images: Path,
) -> None:
    """Test extract_cover integration for CBZ format.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    cbz_file_with_images : Path
        CBZ file with images.
    """
    result = extractor.extract_cover(cbz_file_with_images)
    assert result is not None
    assert isinstance(result, bytes)


def test_extract_cover_cbc_integration(
    extractor: CbzCoverExtractor,
    cbc_file_with_cbz: Path,
) -> None:
    """Test extract_cover integration for CBC format.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    cbc_file_with_cbz : Path
        CBC file containing CBZ.
    """
    result = extractor.extract_cover(cbc_file_with_cbz)
    assert result is not None
    assert isinstance(result, bytes)


def test_extraction_strategies_initialized(extractor: CbzCoverExtractor) -> None:
    """Test that extraction strategies are properly initialized.

    Parameters
    ----------
    extractor : CbzCoverExtractor
        Extractor instance.
    """
    assert len(extractor._extraction_strategies) == 4
    assert ".cbz" in extractor._extraction_strategies
    assert ".cbr" in extractor._extraction_strategies
    assert ".cb7" in extractor._extraction_strategies
    assert ".cbc" in extractor._extraction_strategies
