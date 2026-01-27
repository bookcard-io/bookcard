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

import shutil
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from PIL import Image

from bookcard.models.media import Data
from bookcard.repositories.file_manager import CalibreFileManager

if TYPE_CHECKING:
    from tests.conftest import DummySession


@pytest.fixture
def file_manager() -> CalibreFileManager:
    """Create a CalibreFileManager instance."""
    return CalibreFileManager()


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

        with patch("bookcard.repositories.file_manager.Image.open") as mock_open:
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
            session=session,  # type: ignore[invalid-argument-type]
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
            session=session,  # type: ignore[invalid-argument-type]
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


class TestCalibreFileManagerMoveBookDirectory:
    """Test move_book_directory method."""

    def test_move_book_directory_same_path(
        self,
        file_manager: CalibreFileManager,
        tmp_library_path: Path,
    ) -> None:
        """Test move_book_directory skips move when paths are the same (covers lines 288-290)."""
        book_path = "Author/Title"
        book_dir = tmp_library_path / book_path
        book_dir.mkdir(parents=True)

        # Should not raise and should not move anything
        file_manager.move_book_directory(
            old_book_path=book_path,
            new_book_path=book_path,
            library_path=tmp_library_path,
        )

        assert book_dir.exists()

    def test_move_book_directory_old_dir_not_exists(
        self,
        file_manager: CalibreFileManager,
        tmp_library_path: Path,
    ) -> None:
        """Test move_book_directory creates new directory when old doesn't exist (covers lines 293-299)."""
        old_path = "Author/Old Title"
        new_path = "Author/New Title"

        file_manager.move_book_directory(
            old_book_path=old_path,
            new_book_path=new_path,
            library_path=tmp_library_path,
        )

        new_dir = tmp_library_path / new_path
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_move_book_directory_old_dir_is_file(
        self,
        file_manager: CalibreFileManager,
        tmp_library_path: Path,
    ) -> None:
        """Test move_book_directory handles old path being a file (covers lines 293-299)."""
        old_path = "Author/Old Title"
        new_path = "Author/New Title"
        old_file = tmp_library_path / old_path
        old_file.parent.mkdir(parents=True)
        old_file.touch()

        file_manager.move_book_directory(
            old_book_path=old_path,
            new_book_path=new_path,
            library_path=tmp_library_path,
        )

        new_dir = tmp_library_path / new_path
        assert new_dir.exists()

    def test_move_book_directory_new_dir_exists_with_files(
        self,
        file_manager: CalibreFileManager,
        tmp_library_path: Path,
    ) -> None:
        """Test move_book_directory handles new directory already existing (covers lines 302-309)."""
        old_path = "Author/Old Title"
        new_path = "Author/New Title"
        old_dir = tmp_library_path / old_path
        new_dir = tmp_library_path / new_path

        old_dir.mkdir(parents=True)
        old_file = old_dir / "book.epub"
        old_file.write_bytes(b"content")

        new_dir.mkdir(parents=True)
        existing_file = new_dir / "existing.epub"
        existing_file.write_bytes(b"existing")

        file_manager.move_book_directory(
            old_book_path=old_path,
            new_book_path=new_path,
            library_path=tmp_library_path,
        )

        # File should be moved
        moved_file = new_dir / "book.epub"
        assert moved_file.exists()
        assert moved_file.read_bytes() == b"content"

    def test_move_book_directory_moves_files(
        self,
        file_manager: CalibreFileManager,
        tmp_library_path: Path,
    ) -> None:
        """Test move_book_directory moves all files (covers lines 314-340)."""
        old_path = "Author/Old Title"
        new_path = "Author/New Title"
        old_dir = tmp_library_path / old_path
        new_dir = tmp_library_path / new_path

        old_dir.mkdir(parents=True)
        file1 = old_dir / "book.epub"
        file1.write_bytes(b"content1")
        file2 = old_dir / "cover.jpg"
        file2.write_bytes(b"content2")

        file_manager.move_book_directory(
            old_book_path=old_path,
            new_book_path=new_path,
            library_path=tmp_library_path,
        )

        # Files should be in new location
        new_file1 = new_dir / "book.epub"
        new_file2 = new_dir / "cover.jpg"
        assert new_file1.exists()
        assert new_file2.exists()
        assert new_file1.read_bytes() == b"content1"
        assert new_file2.read_bytes() == b"content2"

        # Old directory should be cleaned up
        assert not old_dir.exists()

    def test_move_book_directory_overwrites_existing_file(
        self,
        file_manager: CalibreFileManager,
        tmp_library_path: Path,
    ) -> None:
        """Test move_book_directory overwrites existing target file (covers lines 321-324)."""
        old_path = "Author/Old Title"
        new_path = "Author/New Title"
        old_dir = tmp_library_path / old_path
        new_dir = tmp_library_path / new_path

        old_dir.mkdir(parents=True)
        old_file = old_dir / "book.epub"
        old_file.write_bytes(b"new content")

        new_dir.mkdir(parents=True)
        existing_file = new_dir / "book.epub"
        existing_file.write_bytes(b"old content")

        file_manager.move_book_directory(
            old_book_path=old_path,
            new_book_path=new_path,
            library_path=tmp_library_path,
        )

        # File should be overwritten
        moved_file = new_dir / "book.epub"
        assert moved_file.exists()
        assert moved_file.read_bytes() == b"new content"

    def test_move_book_directory_moves_subdirectories(
        self,
        file_manager: CalibreFileManager,
        tmp_library_path: Path,
    ) -> None:
        """Test move_book_directory moves subdirectories (covers lines 328-333)."""
        old_path = "Author/Old Title"
        new_path = "Author/New Title"
        old_dir = tmp_library_path / old_path
        new_dir = tmp_library_path / new_path

        old_dir.mkdir(parents=True)
        subdir = old_dir / "subdir"
        subdir.mkdir()
        subfile = subdir / "file.txt"
        subfile.write_bytes(b"content")

        file_manager.move_book_directory(
            old_book_path=old_path,
            new_book_path=new_path,
            library_path=tmp_library_path,
        )

        # Subdirectory should be moved
        new_subdir = new_dir / "subdir"
        assert new_subdir.exists()
        new_subfile = new_subdir / "file.txt"
        assert new_subfile.exists()

    def test_move_book_directory_handles_os_error(
        self,
        file_manager: CalibreFileManager,
        tmp_library_path: Path,
    ) -> None:
        """Test move_book_directory handles OSError (covers lines 341-347)."""
        old_path = "Author/Old Title"
        new_path = "Author/New Title"
        old_dir = tmp_library_path / old_path
        old_dir.mkdir(parents=True)
        # Create a file so shutil.move is actually called
        old_file = old_dir / "book.epub"
        old_file.write_bytes(b"content")

        with patch("shutil.move") as mock_move:
            mock_move.side_effect = OSError("Permission denied")

            with pytest.raises(OSError, match="Permission denied"):
                file_manager.move_book_directory(
                    old_book_path=old_path,
                    new_book_path=new_path,
                    library_path=tmp_library_path,
                )

    def test_move_book_directory_handles_shutil_error(
        self,
        file_manager: CalibreFileManager,
        tmp_library_path: Path,
    ) -> None:
        """Test move_book_directory handles shutil.Error (covers lines 341-347)."""
        old_path = "Author/Old Title"
        new_path = "Author/New Title"
        old_dir = tmp_library_path / old_path
        old_dir.mkdir(parents=True)
        # Create a file so shutil.move is actually called
        old_file = old_dir / "book.epub"
        old_file.write_bytes(b"content")

        with patch("shutil.move") as mock_move:
            mock_move.side_effect = shutil.Error("Move failed")

            with pytest.raises(shutil.Error, match="Move failed"):
                file_manager.move_book_directory(
                    old_book_path=old_path,
                    new_book_path=new_path,
                    library_path=tmp_library_path,
                )

    def test_cleanup_empty_directories(
        self,
        file_manager: CalibreFileManager,
        tmp_library_path: Path,
    ) -> None:
        """Test _cleanup_empty_directories removes empty directories (covers lines 365-391)."""
        # Create directory structure with nested levels
        # library_path/Level1/Level2/Level3
        level1 = tmp_library_path / "Level1"
        level2 = level1 / "Level2"
        level3 = level2 / "Level3"
        level3.mkdir(parents=True)

        # Create a file to move
        file1 = level3 / "book.epub"
        file1.write_bytes(b"content")

        # Move file out
        file1.unlink()

        # Cleanup should remove empty directories
        file_manager._cleanup_empty_directories(level3, tmp_library_path)

        # level3 and level2 should be removed
        # level1 should remain because its parent is library_path (stopping condition)
        assert not level3.exists()
        assert not level2.exists()
        # level1 remains because cleanup stops when parent == library_path
        assert level1.exists()

    def test_cleanup_empty_directories_stops_at_non_empty(
        self,
        file_manager: CalibreFileManager,
        tmp_library_path: Path,
    ) -> None:
        """Test _cleanup_empty_directories stops at non-empty directory (covers lines 377-384)."""
        # Create directory structure
        author_dir = tmp_library_path / "Author"
        book_dir1 = author_dir / "Title1"
        book_dir2 = author_dir / "Title2"
        book_dir1.mkdir(parents=True)
        book_dir2.mkdir(parents=True)

        # Create a file in book_dir2
        file2 = book_dir2 / "book.epub"
        file2.write_bytes(b"content")

        # Cleanup book_dir1 (empty)
        file_manager._cleanup_empty_directories(book_dir1, tmp_library_path)

        # book_dir1 should be removed, but author_dir should remain (has book_dir2)
        assert not book_dir1.exists()
        assert author_dir.exists()
        assert book_dir2.exists()

    def test_cleanup_empty_directories_stops_at_library_path(
        self,
        file_manager: CalibreFileManager,
        tmp_library_path: Path,
    ) -> None:
        """Test _cleanup_empty_directories stops at library_path (covers lines 369)."""
        # Create directory structure
        author_dir = tmp_library_path / "Author"
        book_dir = author_dir / "Title"
        book_dir.mkdir(parents=True)

        # Cleanup should stop when parent == library_path
        # The condition is: current_dir.parent != library_path
        # So when current_dir.parent == library_path, it stops
        file_manager._cleanup_empty_directories(book_dir, tmp_library_path)

        # book_dir should be removed
        # author_dir should remain because its parent is library_path (stopping condition)
        assert not book_dir.exists()
        # author_dir remains because cleanup stops when parent == library_path
        assert author_dir.exists()
        assert tmp_library_path.exists()

    def test_cleanup_empty_directories_handles_os_error(
        self,
        file_manager: CalibreFileManager,
        tmp_library_path: Path,
    ) -> None:
        """Test _cleanup_empty_directories handles OSError (covers lines 385-388)."""
        book_dir = tmp_library_path / "Author" / "Title"
        book_dir.mkdir(parents=True)

        with patch.object(Path, "rmdir") as mock_rmdir:
            mock_rmdir.side_effect = OSError("Permission denied")

            # Should not raise, just log warning
            file_manager._cleanup_empty_directories(book_dir, tmp_library_path)

    def test_cleanup_empty_directories_handles_nonexistent_dir(
        self,
        file_manager: CalibreFileManager,
        tmp_library_path: Path,
    ) -> None:
        """Test _cleanup_empty_directories handles nonexistent directory (covers lines 372-384)."""
        book_dir = tmp_library_path / "Author" / "Title"

        # Directory doesn't exist
        file_manager._cleanup_empty_directories(book_dir, tmp_library_path)

        # Should not raise
        assert not book_dir.exists()

    def test_cleanup_empty_directories_handles_not_dir(
        self,
        file_manager: CalibreFileManager,
        tmp_library_path: Path,
    ) -> None:
        """Test _cleanup_empty_directories handles path that is not a directory (covers lines 372-384)."""
        book_dir = tmp_library_path / "Author" / "Title"
        book_dir.parent.mkdir(parents=True)
        book_dir.touch()  # Create as file

        # Should not raise, just skip
        file_manager._cleanup_empty_directories(book_dir, tmp_library_path)
