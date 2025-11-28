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

"""Tests for file manager to achieve 100% coverage."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from fundamental.models.media import Data
from fundamental.repositories.file_manager import CalibreFileManager
from tests.conftest import DummySession


@pytest.fixture
def file_manager() -> CalibreFileManager:
    """Create a CalibreFileManager instance."""
    return CalibreFileManager()


@pytest.fixture
def session() -> DummySession:
    """Create a dummy database session."""
    return DummySession()


@pytest.fixture
def tmp_library_path(tmp_path: Path) -> Path:
    """Create a temporary library path."""
    library_path = tmp_path / "library"
    library_path.mkdir()
    return library_path


class TestCalibreFileManagerSaveBookFile:
    """Test save_book_file method."""

    def test_save_book_file(
        self,
        file_manager: CalibreFileManager,
        tmp_path: Path,
        tmp_library_path: Path,
    ) -> None:
        """Test save_book_file saves file to correct location."""
        source_file = tmp_path / "source.epub"
        source_file.write_bytes(b"test content")

        file_manager.save_book_file(
            file_path=source_file,
            library_path=tmp_library_path,
            book_path_str="Author/Title",
            title_dir="Title",
            file_format="EPUB",
        )

        target_file = tmp_library_path / "Author/Title/Title.epub"
        assert target_file.exists()
        assert target_file.read_bytes() == b"test content"

    @pytest.mark.parametrize(
        ("file_format", "expected_extension"),
        [
            ("EPUB", ".epub"),
            ("epub", ".epub"),
            ("PDF", ".pdf"),
            ("MOBI", ".mobi"),
        ],
    )
    def test_save_book_file_format_lowercase(
        self,
        file_manager: CalibreFileManager,
        tmp_path: Path,
        tmp_library_path: Path,
        file_format: str,
        expected_extension: str,
    ) -> None:
        """Test save_book_file converts format to lowercase."""
        source_file = tmp_path / f"source{expected_extension}"
        source_file.write_bytes(b"test content")

        file_manager.save_book_file(
            file_path=source_file,
            library_path=tmp_library_path,
            book_path_str="Author/Title",
            title_dir="Title",
            file_format=file_format,
        )

        target_file = tmp_library_path / f"Author/Title/Title{expected_extension}"
        assert target_file.exists()


class TestCalibreFileManagerSaveBookCover:
    """Test save_book_cover method."""

    def test_save_book_cover_success_rgb(
        self,
        file_manager: CalibreFileManager,
        tmp_library_path: Path,
    ) -> None:
        """Test save_book_cover saves RGB image successfully."""
        # Create RGB image
        img = Image.new("RGB", (100, 100), color="red")
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        cover_data = img_bytes.getvalue()

        result = file_manager.save_book_cover(
            cover_data=cover_data,
            library_path=tmp_library_path,
            book_path_str="Author/Title",
        )

        assert result is True
        cover_path = tmp_library_path / "Author/Title/cover.jpg"
        assert cover_path.exists()
        # Verify it's a valid JPEG
        saved_img = Image.open(cover_path)
        assert saved_img.format == "JPEG"
        assert saved_img.mode == "RGB"

    def test_save_book_cover_success_converts_mode(
        self,
        file_manager: CalibreFileManager,
        tmp_library_path: Path,
    ) -> None:
        """Test save_book_cover converts non-RGB images to RGB."""
        # Create RGBA image
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        cover_data = img_bytes.getvalue()

        result = file_manager.save_book_cover(
            cover_data=cover_data,
            library_path=tmp_library_path,
            book_path_str="Author/Title",
        )

        assert result is True
        cover_path = tmp_library_path / "Author/Title/cover.jpg"
        assert cover_path.exists()
        saved_img = Image.open(cover_path)
        assert saved_img.mode == "RGB"

    @pytest.mark.parametrize(
        "exception",
        [
            OSError("File error"),
            ValueError("Invalid image"),
            TypeError("Type error"),
            AttributeError("Attribute error"),
        ],
    )
    def test_save_book_cover_handles_exceptions(
        self,
        file_manager: CalibreFileManager,
        tmp_library_path: Path,
        exception: Exception,
    ) -> None:
        """Test save_book_cover handles exceptions gracefully."""
        cover_data = b"invalid image data"

        with patch("fundamental.repositories.file_manager.Image.open") as mock_open:
            mock_open.side_effect = exception

            result = file_manager.save_book_cover(
                cover_data=cover_data,
                library_path=tmp_library_path,
                book_path_str="Author/Title",
            )

            assert result is False


class TestCalibreFileManagerCollectBookFiles:
    """Test collect_book_files method."""

    def test_collect_book_files_directory_not_exists(
        self,
        file_manager: CalibreFileManager,
        session: DummySession,
        tmp_library_path: Path,
    ) -> None:
        """Test collect_book_files handles non-existent directory."""
        files, book_dir = file_manager.collect_book_files(
            session=session,  # type: ignore[arg-type]  # type: ignore[valid-type]
            book_id=1,
            book_path="Nonexistent/Path",
            library_path=tmp_library_path,
        )

        assert files == []
        assert book_dir is None

    def test_collect_book_files_directory_not_dir(
        self,
        file_manager: CalibreFileManager,
        session: DummySession,
        tmp_library_path: Path,
    ) -> None:
        """Test collect_book_files handles path that is not a directory."""
        # Create a file instead of directory
        file_path = tmp_library_path / "not_a_dir"
        file_path.touch()

        files, book_dir = file_manager.collect_book_files(
            session=session,  # type: ignore[arg-type]  # type: ignore[valid-type]
            book_id=1,
            book_path="not_a_dir",
            library_path=tmp_library_path,
        )

        assert files == []
        assert book_dir is None

    def test_collect_book_files_pattern1(
        self,
        file_manager: CalibreFileManager,
        session: DummySession,
        tmp_library_path: Path,
    ) -> None:
        """Test collect_book_files finds files using pattern 1."""
        book_dir = tmp_library_path / "Author/Title"
        book_dir.mkdir(parents=True)

        # Create file matching pattern 1
        file1 = book_dir / "Book Title.epub"
        file1.write_bytes(b"content")

        data = Data(
            id=1,
            book=1,
            format="EPUB",
            uncompressed_size=1000,
            name="Book Title",
        )
        session.set_exec_result([data])

        files, returned_book_dir = file_manager.collect_book_files(
            session=session,  # type: ignore[valid-type]
            book_id=1,
            book_path="Author/Title",
            library_path=tmp_library_path,
        )

        assert len(files) == 1
        assert file1 in files
        assert returned_book_dir == book_dir

    def test_collect_book_files_pattern2(
        self,
        file_manager: CalibreFileManager,
        session: DummySession,
        tmp_library_path: Path,
    ) -> None:
        """Test collect_book_files finds files using pattern 2."""
        book_dir = tmp_library_path / "Author/Title"
        book_dir.mkdir(parents=True)

        # Create file matching pattern 2 (book_id.format)
        file1 = book_dir / "1.epub"
        file1.write_bytes(b"content")

        data = Data(
            id=1,
            book=1,
            format="EPUB",
            uncompressed_size=1000,
            name="Book Title",
        )
        session.set_exec_result([data])

        files, returned_book_dir = file_manager.collect_book_files(
            session=session,  # type: ignore[valid-type]
            book_id=1,
            book_path="Author/Title",
            library_path=tmp_library_path,
        )

        assert len(files) == 1
        assert file1 in files
        assert returned_book_dir == book_dir

    def test_collect_book_files_both_patterns(
        self,
        file_manager: CalibreFileManager,
        session: DummySession,
        tmp_library_path: Path,
    ) -> None:
        """Test collect_book_files finds files using both patterns."""
        book_dir = tmp_library_path / "Author/Title"
        book_dir.mkdir(parents=True)

        # Create files matching both patterns
        file1 = book_dir / "Book Title.epub"
        file1.write_bytes(b"content1")
        file2 = book_dir / "1.epub"
        file2.write_bytes(b"content2")

        data = Data(
            id=1,
            book=1,
            format="EPUB",
            uncompressed_size=1000,
            name="Book Title",
        )
        session.set_exec_result([data])

        files, _returned_book_dir = file_manager.collect_book_files(
            session=session,  # type: ignore[valid-type]
            book_id=1,
            book_path="Author/Title",
            library_path=tmp_library_path,
        )

        # Both files should be included (pattern 1 first, then pattern 2 if not already in list)
        assert len(files) == 2
        assert file1 in files
        assert file2 in files

    def test_collect_book_files_no_name(
        self,
        file_manager: CalibreFileManager,
        session: DummySession,
        tmp_library_path: Path,
    ) -> None:
        """Test collect_book_files handles Data record with no name."""
        book_dir = tmp_library_path / "Author/Title"
        book_dir.mkdir(parents=True)

        # Create file matching pattern 2 (book_id.format)
        file1 = book_dir / "1.epub"
        file1.write_bytes(b"content")

        data = Data(
            id=1,
            book=1,
            format="EPUB",
            uncompressed_size=1000,
            name=None,
        )
        session.set_exec_result([data])

        files, _returned_book_dir = file_manager.collect_book_files(
            session=session,  # type: ignore[valid-type]
            book_id=1,
            book_path="Author/Title",
            library_path=tmp_library_path,
        )

        assert len(files) == 1
        assert file1 in files

    def test_collect_book_files_multiple_formats(
        self,
        file_manager: CalibreFileManager,
        session: DummySession,
        tmp_library_path: Path,
    ) -> None:
        """Test collect_book_files handles multiple file formats."""
        book_dir = tmp_library_path / "Author/Title"
        book_dir.mkdir(parents=True)

        file1 = book_dir / "Book Title.epub"
        file1.write_bytes(b"content1")
        file2 = book_dir / "Book Title.pdf"
        file2.write_bytes(b"content2")

        data1 = Data(
            id=1,
            book=1,
            format="EPUB",
            uncompressed_size=1000,
            name="Book Title",
        )
        data2 = Data(
            id=2,
            book=1,
            format="PDF",
            uncompressed_size=2000,
            name="Book Title",
        )
        session.set_exec_result([data1, data2])

        files, _returned_book_dir = file_manager.collect_book_files(
            session=session,  # type: ignore[valid-type]
            book_id=1,
            book_path="Author/Title",
            library_path=tmp_library_path,
        )

        assert len(files) == 2
        assert file1 in files
        assert file2 in files

    def test_collect_book_files_includes_cover(
        self,
        file_manager: CalibreFileManager,
        session: DummySession,
        tmp_library_path: Path,
    ) -> None:
        """Test collect_book_files includes cover.jpg if it exists."""
        book_dir = tmp_library_path / "Author/Title"
        book_dir.mkdir(parents=True)

        cover = book_dir / "cover.jpg"
        cover.write_bytes(b"cover content")

        session.set_exec_result([])

        files, returned_book_dir = file_manager.collect_book_files(
            session=session,  # type: ignore[valid-type]
            book_id=1,
            book_path="Author/Title",
            library_path=tmp_library_path,
        )

        assert cover in files
        assert returned_book_dir == book_dir

    def test_collect_book_files_oserror_listing(
        self,
        file_manager: CalibreFileManager,
        session: DummySession,
        tmp_library_path: Path,
    ) -> None:
        """Test collect_book_files handles OSError when listing files."""
        book_dir = tmp_library_path / "Author/Title"
        book_dir.mkdir(parents=True)

        session.set_exec_result([])

        with patch.object(Path, "iterdir") as mock_iterdir:
            mock_iterdir.side_effect = OSError("Permission denied")

            _files, returned_book_dir = file_manager.collect_book_files(
                session=session,  # type: ignore[valid-type]
                book_id=1,
                book_path="Author/Title",
                library_path=tmp_library_path,
            )

            # Should still work, just without extension matching
            assert returned_book_dir == book_dir

    def test_collect_book_files_extension_matching(
        self,
        file_manager: CalibreFileManager,
        session: DummySession,
        tmp_library_path: Path,
    ) -> None:
        """Test collect_book_files uses extension matching as fallback."""
        book_dir = tmp_library_path / "Author/Title"
        book_dir.mkdir(parents=True)

        # Create file with different name but correct extension
        file1 = book_dir / "different_name.epub"
        file1.write_bytes(b"content")

        data = Data(
            id=1,
            book=1,
            format="EPUB",
            uncompressed_size=1000,
            name="Book Title",
        )
        session.set_exec_result([data])

        files, _returned_book_dir = file_manager.collect_book_files(
            session=session,  # type: ignore[valid-type]
            book_id=1,
            book_path="Author/Title",
            library_path=tmp_library_path,
        )

        assert len(files) == 1
        assert file1 in files


class TestCalibreFileManagerMatchFilesByExtension:
    """Test _match_files_by_extension method."""

    def test_match_files_by_extension_no_data_records(
        self,
        file_manager: CalibreFileManager,
    ) -> None:
        """Test _match_files_by_extension returns empty when no data records."""
        all_files = [Path("file1.epub"), Path("file2.pdf")]
        result = file_manager._match_files_by_extension(
            all_files=all_files,
            data_records=[],
            existing_paths=[],
            book_id=1,
        )

        assert result == []

    def test_match_files_by_extension_no_files(
        self,
        file_manager: CalibreFileManager,
    ) -> None:
        """Test _match_files_by_extension returns empty when no files."""
        data = Data(
            id=1,
            book=1,
            format="EPUB",
            uncompressed_size=1000,
            name="Book",
        )
        result = file_manager._match_files_by_extension(
            all_files=[],
            data_records=[data],
            existing_paths=[],
            book_id=1,
        )

        assert result == []

    def test_match_files_by_extension_matches(
        self,
        file_manager: CalibreFileManager,
    ) -> None:
        """Test _match_files_by_extension matches files by extension."""
        all_files = [
            Path("file1.epub"),
            Path("file2.pdf"),
            Path("file3.mobi"),
        ]
        data1 = Data(
            id=1,
            book=1,
            format="EPUB",
            uncompressed_size=1000,
            name="Book",
        )
        data2 = Data(
            id=2,
            book=1,
            format="PDF",
            uncompressed_size=2000,
            name="Book",
        )

        result = file_manager._match_files_by_extension(
            all_files=all_files,
            data_records=[data1, data2],
            existing_paths=[],
            book_id=1,
        )

        assert len(result) == 2
        assert Path("file1.epub") in result
        assert Path("file2.pdf") in result
        assert Path("file3.mobi") not in result

    def test_match_files_by_extension_excludes_existing(
        self,
        file_manager: CalibreFileManager,
    ) -> None:
        """Test _match_files_by_extension excludes already matched files."""
        all_files = [Path("file1.epub"), Path("file2.epub")]
        data = Data(
            id=1,
            book=1,
            format="EPUB",
            uncompressed_size=1000,
            name="Book",
        )
        existing_paths = [Path("file1.epub")]

        result = file_manager._match_files_by_extension(
            all_files=all_files,
            data_records=[data],
            existing_paths=existing_paths,
            book_id=1,
        )

        assert len(result) == 1
        assert Path("file2.epub") in result
        assert Path("file1.epub") not in result

    def test_match_files_by_extension_case_insensitive(
        self,
        file_manager: CalibreFileManager,
    ) -> None:
        """Test _match_files_by_extension is case-insensitive."""
        all_files = [Path("file1.EPUB"), Path("file2.PDF")]
        data1 = Data(
            id=1,
            book=1,
            format="epub",
            uncompressed_size=1000,
            name="Book",
        )
        data2 = Data(
            id=2,
            book=1,
            format="pdf",
            uncompressed_size=2000,
            name="Book",
        )

        result = file_manager._match_files_by_extension(
            all_files=all_files,
            data_records=[data1, data2],
            existing_paths=[],
            book_id=1,
        )

        assert len(result) == 2
