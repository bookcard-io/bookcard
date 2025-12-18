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

"""Tests for comic_archive_service to achieve 100% coverage."""

from __future__ import annotations

import zipfile
from io import BytesIO
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from pathlib import Path

import pytest
from PIL import Image

from bookcard.services.comic.comic_archive_service import (
    ComicArchiveService,
    ComicPage,
    ComicPageInfo,
    _natural_sort_key,
)


class TestNaturalSortKey:
    """Test _natural_sort_key function."""

    @pytest.mark.parametrize(
        ("filename", "expected_types"),
        [
            ("page1.jpg", (str, int, str)),
            ("page10.jpg", (str, int, str)),
            ("page_001.jpg", (str, int, str)),
            ("page_10.jpg", (str, int, str)),
            ("cover.jpg", (str,)),
            ("page1a.jpg", (str, int, str)),
        ],
    )
    def test_natural_sort_key(self, filename: str, expected_types: tuple) -> None:
        """Test natural sort key generation.

        Parameters
        ----------
        filename : str
            Filename to test.
        expected_types : tuple
            Expected types for each part.
        """
        result = _natural_sort_key(filename)
        assert len(result) == len(expected_types)
        # Check that numeric parts are ints and string parts are lowercase
        for part, expected_type in zip(result, expected_types, strict=True):
            assert isinstance(part, expected_type)
            if isinstance(part, str):
                assert part == part.lower()  # Should be lowercase


class TestComicArchiveService:
    """Test ComicArchiveService class."""

    @pytest.fixture
    def service(self) -> ComicArchiveService:
        """Create service instance.

        Returns
        -------
        ComicArchiveService
            Service instance.
        """
        return ComicArchiveService()

    @pytest.fixture
    def sample_image(self) -> bytes:
        """Create sample image data.

        Returns
        -------
        bytes
            PNG image data.
        """
        img = Image.new("RGB", (100, 100), color="red")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def test_is_comic_format_valid(self, service: ComicArchiveService) -> None:
        """Test is_comic_format with valid formats.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        """
        assert service.is_comic_format("CBZ") is True
        assert service.is_comic_format("CBR") is True
        assert service.is_comic_format("CB7") is True
        assert service.is_comic_format("CBC") is True
        assert service.is_comic_format(".cbz") is True
        assert service.is_comic_format("cbz") is True

    def test_is_comic_format_invalid(self, service: ComicArchiveService) -> None:
        """Test is_comic_format with invalid formats.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        """
        assert service.is_comic_format("EPUB") is False
        assert service.is_comic_format("PDF") is False
        assert service.is_comic_format("") is False

    def test_list_pages_unsupported_format(
        self, service: ComicArchiveService, tmp_path: Path
    ) -> None:
        """Test list_pages with unsupported format.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        """
        file_path = tmp_path / "test.epub"
        file_path.write_bytes(b"fake")

        with pytest.raises(ValueError, match="Unsupported comic format"):
            service.list_pages(file_path)

    def test_list_pages_extraction_error(
        self, service: ComicArchiveService, tmp_path: Path
    ) -> None:
        """Test list_pages when extraction fails.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        """
        file_path = tmp_path / "test.cbz"
        file_path.write_bytes(b"invalid zip")

        with pytest.raises(ValueError, match="Failed to list pages"):
            service.list_pages(file_path)

    def test_list_cbz_pages(
        self, service: ComicArchiveService, tmp_path: Path, sample_image: bytes
    ) -> None:
        """Test _list_cbz_pages.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        sample_image : bytes
            Sample image data.
        """
        cbz_file = tmp_path / "test.cbz"
        with zipfile.ZipFile(cbz_file, "w") as zf:
            zf.writestr("page1.jpg", sample_image)
            zf.writestr("page2.png", sample_image)
            zf.writestr("dir/", "")  # Directory entry
            zf.writestr("readme.txt", b"text")

        pages = service._list_cbz_pages(cbz_file)
        assert "page1.jpg" in pages
        assert "page2.png" in pages
        assert "dir/" not in pages
        assert "readme.txt" not in pages

    def test_list_cbr_pages(self, service: ComicArchiveService, tmp_path: Path) -> None:
        """Test _list_cbr_pages.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        """
        cbr_file = tmp_path / "test.cbr"
        cbr_file.write_bytes(b"fake rar")

        # Mock rarfile
        with patch("rarfile.RarFile") as mock_rar:
            mock_rar_instance = MagicMock()
            mock_rar_instance.namelist.return_value = ["page1.jpg", "page2.png", "dir/"]
            mock_rar.return_value.__enter__.return_value = mock_rar_instance

            pages = service._list_cbr_pages(cbr_file)
            assert "page1.jpg" in pages
            assert "page2.png" in pages
            assert "dir/" not in pages

    def test_list_cb7_pages(self, service: ComicArchiveService, tmp_path: Path) -> None:
        """Test _list_cb7_pages.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        """
        cb7_file = tmp_path / "test.cb7"
        cb7_file.write_bytes(b"fake 7z")

        # Mock py7zr
        with patch("py7zr.SevenZipFile") as mock_7z:
            mock_7z_instance = MagicMock()
            mock_7z_instance.getnames.return_value = ["page1.jpg", "page2.png", "dir/"]
            mock_7z.return_value.__enter__.return_value = mock_7z_instance

            pages = service._list_cb7_pages(cb7_file)
            assert "page1.jpg" in pages
            assert "page2.png" in pages
            assert "dir/" not in pages

    def test_list_cb7_pages_import_error(
        self, service: ComicArchiveService, tmp_path: Path
    ) -> None:
        """Test _list_cb7_pages when py7zr is not available.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        """
        cb7_file = tmp_path / "test.cb7"
        cb7_file.write_bytes(b"fake 7z")

        with (
            patch(
                "builtins.__import__", side_effect=ImportError("No module named py7zr")
            ),
            pytest.raises(ImportError, match="py7zr library required"),
        ):
            service._list_cb7_pages(cb7_file)

    def test_list_cbc_pages(
        self, service: ComicArchiveService, tmp_path: Path, sample_image: bytes
    ) -> None:
        """Test _list_cbc_pages.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        sample_image : bytes
            Sample image data.
        """
        # Create a CBC (ZIP containing CBZ)
        cbc_file = tmp_path / "test.cbc"

        # Create a CBZ file
        cbz_file = tmp_path / "inner.cbz"
        with zipfile.ZipFile(cbz_file, "w") as zf:
            zf.writestr("page1.jpg", sample_image)
            zf.writestr("page2.png", sample_image)

        # Create CBC containing the CBZ
        with zipfile.ZipFile(cbc_file, "w") as cbc_zip:
            cbc_zip.write(cbz_file, "inner.cbz")

        pages = service._list_cbc_pages(cbc_file)
        assert "page1.jpg" in pages
        assert "page2.png" in pages

    def test_list_cbc_pages_no_cbz(
        self, service: ComicArchiveService, tmp_path: Path
    ) -> None:
        """Test _list_cbc_pages when no CBZ files found.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        """
        cbc_file = tmp_path / "test.cbc"
        with zipfile.ZipFile(cbc_file, "w") as cbc_zip:
            cbc_zip.writestr("readme.txt", b"text")

        pages = service._list_cbc_pages(cbc_file)
        assert pages == []

    def test_get_page_invalid_range(
        self, service: ComicArchiveService, tmp_path: Path, sample_image: bytes
    ) -> None:
        """Test get_page with invalid page number.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        sample_image : bytes
            Sample image data.
        """
        cbz_file = tmp_path / "test.cbz"
        with zipfile.ZipFile(cbz_file, "w") as zf:
            zf.writestr("page1.jpg", sample_image)

        with pytest.raises(IndexError, match="out of range"):
            service.get_page(cbz_file, 0)

        with pytest.raises(IndexError, match="out of range"):
            service.get_page(cbz_file, 2)

    def test_get_page_unsupported_format(
        self, service: ComicArchiveService, tmp_path: Path
    ) -> None:
        """Test get_page with unsupported format.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        """
        file_path = tmp_path / "test.epub"
        file_path.write_bytes(b"fake")

        # Mock list_pages to return pages so we can test the format check
        with (
            patch.object(
                service,
                "list_pages",
                return_value=[ComicPageInfo(page_number=1, filename="page1.jpg")],
            ),
            pytest.raises(ValueError, match="Unsupported comic format"),
        ):
            service.get_page(file_path, 1)

    def test_get_page_image_read_error(
        self, service: ComicArchiveService, tmp_path: Path
    ) -> None:
        """Test get_page when image cannot be read.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        """
        cbz_file = tmp_path / "test.cbz"
        with zipfile.ZipFile(cbz_file, "w") as zf:
            zf.writestr("page1.jpg", b"invalid image data")

        with pytest.raises(ValueError, match="Failed to read image dimensions"):
            service.get_page(cbz_file, 1)

    def test_extract_cbz_page(
        self, service: ComicArchiveService, tmp_path: Path, sample_image: bytes
    ) -> None:
        """Test _extract_cbz_page.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        sample_image : bytes
            Sample image data.
        """
        cbz_file = tmp_path / "test.cbz"
        with zipfile.ZipFile(cbz_file, "w") as zf:
            zf.writestr("page1.jpg", sample_image)

        data = service._extract_cbz_page(cbz_file, "page1.jpg")
        assert data == sample_image

    def test_extract_cbr_page(
        self, service: ComicArchiveService, tmp_path: Path, sample_image: bytes
    ) -> None:
        """Test _extract_cbr_page.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        sample_image : bytes
            Sample image data.
        """
        cbr_file = tmp_path / "test.cbr"
        cbr_file.write_bytes(b"fake rar")

        with patch("rarfile.RarFile") as mock_rar:
            mock_rar_instance = MagicMock()
            mock_rar_instance.read.return_value = sample_image
            mock_rar.return_value.__enter__.return_value = mock_rar_instance

            data = service._extract_cbr_page(cbr_file, "page1.jpg")
            assert data == sample_image

    def test_extract_cbr_page_import_error(
        self, service: ComicArchiveService, tmp_path: Path
    ) -> None:
        """Test _extract_cbr_page when rarfile is not available.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        """
        cbr_file = tmp_path / "test.cbr"
        cbr_file.write_bytes(b"fake rar")

        with (
            patch(
                "builtins.__import__",
                side_effect=ImportError("No module named rarfile"),
            ),
            pytest.raises(ImportError, match="rarfile library required"),
        ):
            service._extract_cbr_page(cbr_file, "page1.jpg")

    def test_extract_cb7_page(
        self, service: ComicArchiveService, tmp_path: Path, sample_image: bytes
    ) -> None:
        """Test _extract_cb7_page.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        sample_image : bytes
            Sample image data.
        """
        cb7_file = tmp_path / "test.cb7"
        cb7_file.write_bytes(b"fake 7z")

        with patch("py7zr.SevenZipFile") as mock_7z:
            mock_7z_instance = MagicMock()
            mock_file_obj = MagicMock()
            mock_file_obj.read.return_value = sample_image
            mock_7z_instance.read.return_value = {"page1.jpg": mock_file_obj}
            mock_7z.return_value.__enter__.return_value = mock_7z_instance

            data = service._extract_cb7_page(cb7_file, "page1.jpg")
            assert data == sample_image

    def test_extract_cb7_page_import_error(
        self, service: ComicArchiveService, tmp_path: Path
    ) -> None:
        """Test _extract_cb7_page when py7zr is not available.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        """
        cb7_file = tmp_path / "test.cb7"
        cb7_file.write_bytes(b"fake 7z")

        with (
            patch(
                "builtins.__import__", side_effect=ImportError("No module named py7zr")
            ),
            pytest.raises(ImportError, match="py7zr library required"),
        ):
            service._extract_cb7_page(cb7_file, "page1.jpg")

    def test_extract_cbc_page(
        self, service: ComicArchiveService, tmp_path: Path, sample_image: bytes
    ) -> None:
        """Test _extract_cbc_page.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        sample_image : bytes
            Sample image data.
        """
        # Create a CBC (ZIP containing CBZ)
        cbc_file = tmp_path / "test.cbc"

        # Create a CBZ file
        cbz_file = tmp_path / "inner.cbz"
        with zipfile.ZipFile(cbz_file, "w") as zf:
            zf.writestr("page1.jpg", sample_image)

        # Create CBC containing the CBZ
        with zipfile.ZipFile(cbc_file, "w") as cbc_zip:
            cbc_zip.write(cbz_file, "inner.cbz")

        data = service._extract_cbc_page(cbc_file, "page1.jpg")
        assert data == sample_image

    def test_extract_cbc_page_no_cbz(
        self, service: ComicArchiveService, tmp_path: Path
    ) -> None:
        """Test _extract_cbc_page when no CBZ files found.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        """
        cbc_file = tmp_path / "test.cbc"
        with zipfile.ZipFile(cbc_file, "w") as cbc_zip:
            cbc_zip.writestr("readme.txt", b"text")

        with pytest.raises(ValueError, match="No CBZ files found in CBC archive"):
            service._extract_cbc_page(cbc_file, "page1.jpg")

    def test_get_page_full_flow_cbz(
        self, service: ComicArchiveService, tmp_path: Path, sample_image: bytes
    ) -> None:
        """Test full get_page flow with CBZ.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        sample_image : bytes
            Sample image data.
        """
        cbz_file = tmp_path / "test.cbz"
        with zipfile.ZipFile(cbz_file, "w") as zf:
            zf.writestr("page1.jpg", sample_image)
            zf.writestr("page2.png", sample_image)

        page = service.get_page(cbz_file, 1)
        assert isinstance(page, ComicPage)
        assert page.page_number == 1
        assert page.image_data == sample_image
        assert page.width == 100
        assert page.height == 100

    def test_get_page_full_flow_cbr(
        self, service: ComicArchiveService, tmp_path: Path, sample_image: bytes
    ) -> None:
        """Test full get_page flow with CBR.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        sample_image : bytes
            Sample image data.
        """
        cbr_file = tmp_path / "test.cbr"
        cbr_file.write_bytes(b"fake rar")

        with patch("rarfile.RarFile") as mock_rar:
            mock_rar_instance = MagicMock()
            mock_rar_instance.namelist.return_value = ["page1.jpg"]
            mock_rar_instance.read.return_value = sample_image
            mock_rar.return_value.__enter__.return_value = mock_rar_instance

            page = service.get_page(cbr_file, 1)
            assert isinstance(page, ComicPage)
            assert page.page_number == 1
            assert page.image_data == sample_image

    def test_get_page_full_flow_cb7(
        self, service: ComicArchiveService, tmp_path: Path, sample_image: bytes
    ) -> None:
        """Test full get_page flow with CB7.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        sample_image : bytes
            Sample image data.
        """
        cb7_file = tmp_path / "test.cb7"
        cb7_file.write_bytes(b"fake 7z")

        with patch("py7zr.SevenZipFile") as mock_7z:
            mock_7z_instance = MagicMock()
            mock_7z_instance.getnames.return_value = ["page1.jpg"]
            mock_file_obj = MagicMock()
            mock_file_obj.read.return_value = sample_image
            mock_7z_instance.read.return_value = {"page1.jpg": mock_file_obj}
            mock_7z.return_value.__enter__.return_value = mock_7z_instance

            page = service.get_page(cb7_file, 1)
            assert isinstance(page, ComicPage)
            assert page.page_number == 1
            assert page.image_data == sample_image

    def test_get_page_full_flow_cbc(
        self, service: ComicArchiveService, tmp_path: Path, sample_image: bytes
    ) -> None:
        """Test full get_page flow with CBC.

        Parameters
        ----------
        service : ComicArchiveService
            Service instance.
        tmp_path : Path
            Temporary directory path.
        sample_image : bytes
            Sample image data.
        """
        # Create a CBC (ZIP containing CBZ)
        cbc_file = tmp_path / "test.cbc"

        # Create a CBZ file
        cbz_file = tmp_path / "inner.cbz"
        with zipfile.ZipFile(cbz_file, "w") as zf:
            zf.writestr("page1.jpg", sample_image)

        # Create CBC containing the CBZ
        with zipfile.ZipFile(cbc_file, "w") as cbc_zip:
            cbc_zip.write(cbz_file, "inner.cbz")

        page = service.get_page(cbc_file, 1)
        assert isinstance(page, ComicPage)
        assert page.page_number == 1
        assert page.image_data == sample_image
