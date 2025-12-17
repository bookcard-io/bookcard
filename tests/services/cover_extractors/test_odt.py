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

"""Tests for OdtCoverExtractor to achieve 100% coverage."""

from __future__ import annotations

import zipfile
from io import BytesIO
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from bookcard.services.cover_extractors.odt import OdtCoverExtractor

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def extractor() -> OdtCoverExtractor:
    """Create OdtCoverExtractor instance."""
    return OdtCoverExtractor()


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory."""
    return tmp_path


def create_odt_file(
    temp_dir: Path,
    picture_files: list[str] | None = None,
    invalid_zip: bool = False,
) -> Path:
    """Create a mock ODT file for testing.

    Parameters
    ----------
    temp_dir : Path
        Temporary directory path.
    picture_files : list[str] | None
        List of picture file paths to include.
    invalid_zip : bool
        If True, create an invalid ZIP file.

    Returns
    -------
    Path
        Path to the created ODT file.
    """
    odt_path = temp_dir / "test.odt"

    if invalid_zip:
        odt_path.write_bytes(b"invalid zip content")
        return odt_path

    with zipfile.ZipFile(odt_path, "w") as odt_zip:
        if picture_files:
            for pic_file in picture_files:
                # Create a simple image
                img = Image.new("RGB", (100, 100), color="red")
                img_bytes = BytesIO()
                img.save(img_bytes, format="PNG")
                odt_zip.writestr(pic_file, img_bytes.getvalue())

    return odt_path


class TestCanHandle:
    """Test can_handle method."""

    @pytest.mark.parametrize(
        ("file_format", "expected"),
        [
            ("odt", True),
            ("ODT", True),
            (".odt", True),
            ("pdf", False),
            ("epub", False),
            ("docx", False),
        ],
    )
    def test_can_handle(
        self,
        extractor: OdtCoverExtractor,
        file_format: str,
        expected: bool,
    ) -> None:
        """Test can_handle for various formats."""
        assert extractor.can_handle(file_format) == expected


class TestExtractCover:
    """Test extract_cover method."""

    def test_extract_cover_success(
        self,
        extractor: OdtCoverExtractor,
        temp_dir: Path,
    ) -> None:
        """Test successful cover extraction (covers lines 57-75)."""
        odt_path = create_odt_file(
            temp_dir,
            picture_files=["Pictures/cover.jpg", "Pictures/other.png"],
        )

        result = extractor.extract_cover(odt_path)

        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_extract_cover_no_pictures(
        self,
        extractor: OdtCoverExtractor,
        temp_dir: Path,
    ) -> None:
        """Test extract_cover when no pictures found (covers lines 67-68)."""
        odt_path = create_odt_file(temp_dir, picture_files=None)

        result = extractor.extract_cover(odt_path)

        assert result is None

    def test_extract_cover_invalid_zip(
        self,
        extractor: OdtCoverExtractor,
        temp_dir: Path,
    ) -> None:
        """Test extract_cover with invalid ZIP (covers lines 76-77)."""
        odt_path = create_odt_file(temp_dir, invalid_zip=True)

        result = extractor.extract_cover(odt_path)

        assert result is None

    def test_extract_cover_os_error(
        self,
        extractor: OdtCoverExtractor,
        temp_dir: Path,
    ) -> None:
        """Test extract_cover with OSError (covers lines 76-77)."""
        odt_path = temp_dir / "nonexistent.odt"

        result = extractor.extract_cover(odt_path)

        assert result is None

    def test_extract_cover_key_error(
        self,
        extractor: OdtCoverExtractor,
        temp_dir: Path,
    ) -> None:
        """Test extract_cover with KeyError (covers lines 76-77)."""
        odt_path = create_odt_file(temp_dir, picture_files=["Pictures/cover.jpg"])

        with patch("zipfile.ZipFile.read") as mock_read:
            mock_read.side_effect = KeyError("File not found")

            result = extractor.extract_cover(odt_path)

            assert result is None

    def test_extract_cover_filters_image_extensions(
        self,
        extractor: OdtCoverExtractor,
        temp_dir: Path,
    ) -> None:
        """Test extract_cover filters image extensions (covers lines 60-65)."""
        odt_path = create_odt_file(
            temp_dir,
            picture_files=[
                "Pictures/cover.jpg",
                "Pictures/image.jpeg",
                "Pictures/photo.png",
                "Pictures/pic.gif",
                "Pictures/bitmap.bmp",
                "Pictures/document.txt",  # Should be ignored
            ],
        )

        result = extractor.extract_cover(odt_path)

        assert result is not None
        # Should use first image (cover.jpg)


class TestProcessImage:
    """Test _process_image method."""

    def test_process_image_rgb(
        self,
        extractor: OdtCoverExtractor,
    ) -> None:
        """Test _process_image with RGB image (covers lines 92-100)."""
        img = Image.new("RGB", (100, 100), color="red")
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        image_data = img_bytes.getvalue()

        result = extractor._process_image(image_data)

        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_process_image_non_rgb(
        self,
        extractor: OdtCoverExtractor,
    ) -> None:
        """Test _process_image with non-RGB image (covers lines 95-96)."""
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        image_data = img_bytes.getvalue()

        result = extractor._process_image(image_data)

        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_process_image_invalid_data(
        self,
        extractor: OdtCoverExtractor,
    ) -> None:
        """Test _process_image with invalid image data (covers lines 101-102)."""
        invalid_data = b"not an image"

        result = extractor._process_image(invalid_data)

        assert result is None

    def test_process_image_os_error(
        self,
        extractor: OdtCoverExtractor,
    ) -> None:
        """Test _process_image with OSError (covers lines 101-102)."""
        with patch("PIL.Image.open") as mock_open:
            mock_open.side_effect = OSError("Cannot open image")

            result = extractor._process_image(b"fake image data")

            assert result is None

    def test_process_image_value_error(
        self,
        extractor: OdtCoverExtractor,
    ) -> None:
        """Test _process_image with ValueError (covers lines 101-102)."""
        with patch("PIL.Image.open") as mock_open:
            mock_open.side_effect = ValueError("Invalid image")

            result = extractor._process_image(b"fake image data")

            assert result is None

    def test_process_image_type_error(
        self,
        extractor: OdtCoverExtractor,
    ) -> None:
        """Test _process_image with TypeError (covers lines 101-102)."""
        with patch("PIL.Image.open") as mock_open:
            mock_open.side_effect = TypeError("Type error")

            result = extractor._process_image(b"fake image data")

            assert result is None

    def test_process_image_attribute_error(
        self,
        extractor: OdtCoverExtractor,
    ) -> None:
        """Test _process_image with AttributeError (covers lines 101-102)."""
        with patch("PIL.Image.open") as mock_open:
            mock_img = MagicMock()
            del mock_img.convert
            mock_open.return_value = mock_img

            result = extractor._process_image(b"fake image data")

            assert result is None
