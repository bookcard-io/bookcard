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

"""Tests for core EPUB I/O operations."""

import zipfile
from pathlib import Path

import pytest

from bookcard.models.epub_fixer import EPUBFixType
from bookcard.services.epub_fixer.core.epub import (
    EPUBContents,
    EPUBReader,
    EPUBWriter,
    FixResult,
)


def test_epub_contents_defaults() -> None:
    """Test EPUBContents default initialization."""
    contents = EPUBContents()
    assert contents.files == {}
    assert contents.binary_files == {}
    assert contents.entries == []


def test_epub_contents_with_data() -> None:
    """Test EPUBContents with data."""
    contents = EPUBContents(
        files={"file.html": "<html></html>"},
        binary_files={"image.jpg": b"data"},
        entries=["file.html", "image.jpg"],
    )
    assert len(contents.files) == 1
    assert len(contents.binary_files) == 1
    assert len(contents.entries) == 2


def test_fix_result() -> None:
    """Test FixResult dataclass."""
    result = FixResult(
        fix_type=EPUBFixType.ENCODING,
        description="Test fix",
        file_name="file.html",
        original_value="old",
        fixed_value="new",
    )
    assert result.fix_type == EPUBFixType.ENCODING
    assert result.description == "Test fix"
    assert result.file_name == "file.html"
    assert result.original_value == "old"
    assert result.fixed_value == "new"


def test_fix_result_minimal() -> None:
    """Test FixResult with minimal fields."""
    result = FixResult(
        fix_type=EPUBFixType.BODY_ID_LINK,
        description="Test fix",
    )
    assert result.fix_type == EPUBFixType.BODY_ID_LINK
    assert result.description == "Test fix"
    assert result.file_name is None
    assert result.original_value is None
    assert result.fixed_value is None


def test_epub_reader_read_success(minimal_epub: Path) -> None:
    """Test EPUBReader reading valid EPUB."""
    reader = EPUBReader()
    contents = reader.read(minimal_epub)

    assert "mimetype" in contents.files
    assert "META-INF/container.xml" in contents.files
    assert "content.opf" in contents.files
    assert "chapter1.html" in contents.files
    assert len(contents.entries) == 4


def test_epub_reader_read_not_found(temp_dir: Path) -> None:
    """Test EPUBReader with non-existent file."""
    reader = EPUBReader()
    non_existent = temp_dir / "nonexistent.epub"

    with pytest.raises(FileNotFoundError, match="EPUB file not found"):
        reader.read(non_existent)


def test_epub_reader_read_invalid_zip(temp_dir: Path) -> None:
    """Test EPUBReader with invalid ZIP file."""
    reader = EPUBReader()
    invalid_file = temp_dir / "invalid.epub"
    invalid_file.write_text("not a zip file")

    with pytest.raises(zipfile.BadZipFile):
        reader.read(invalid_file)


def test_epub_reader_read_unicode_decode_error(temp_dir: Path) -> None:
    """Test EPUBReader handling Unicode decode errors."""
    epub_path = temp_dir / "unicode_test.epub"

    with zipfile.ZipFile(epub_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
        zip_ref.writestr(
            "mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED
        )
        # Create file with invalid UTF-8 that will fallback to latin-1
        zip_ref.writestr("test.html", b"\xff\xfe<html></html>")

    reader = EPUBReader()
    contents = reader.read(epub_path)

    # Should handle decode error gracefully
    assert "test.html" in contents.files


def test_epub_reader_read_binary_files(minimal_epub: Path) -> None:
    """Test EPUBReader reading binary files."""
    epub_path = Path(minimal_epub)
    # Add binary file to EPUB
    with zipfile.ZipFile(epub_path, "a", zipfile.ZIP_DEFLATED) as zip_ref:
        zip_ref.writestr("image.jpg", b"fake image data")

    reader = EPUBReader()
    contents = reader.read(epub_path)

    assert "image.jpg" in contents.binary_files
    assert contents.binary_files["image.jpg"] == b"fake image data"


def test_epub_writer_write_success(epub_contents: EPUBContents, temp_dir: Path) -> None:
    """Test EPUBWriter writing EPUB."""
    writer = EPUBWriter()
    output_path = temp_dir / "output.epub"

    writer.write(epub_contents, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_epub_writer_write_mimetype_first(
    epub_contents: EPUBContents, temp_dir: Path
) -> None:
    """Test EPUBWriter writes mimetype first and uncompressed."""
    writer = EPUBWriter()
    output_path = temp_dir / "output.epub"

    writer.write(epub_contents, output_path)

    # Verify mimetype is first and uncompressed
    with zipfile.ZipFile(output_path, "r") as zip_ref:
        info_list = zip_ref.infolist()
        assert info_list[0].filename == "mimetype"
        assert info_list[0].compress_type == zipfile.ZIP_STORED


def test_epub_writer_write_all_files(
    epub_contents: EPUBContents, temp_dir: Path
) -> None:
    """Test EPUBWriter writes all files."""
    writer = EPUBWriter()
    output_path = temp_dir / "output.epub"

    writer.write(epub_contents, output_path)

    # Verify all files are written
    with zipfile.ZipFile(output_path, "r") as zip_ref:
        filenames = zip_ref.namelist()
        assert "mimetype" in filenames
        assert "META-INF/container.xml" in filenames
        assert "content.opf" in filenames
        assert "chapter1.html" in filenames
        assert "image.jpg" in filenames


def test_epub_writer_write_roundtrip(minimal_epub: Path, temp_dir: Path) -> None:
    """Test EPUBWriter roundtrip (read -> write -> read)."""
    reader = EPUBReader()
    writer = EPUBWriter()

    # Read original
    contents = reader.read(minimal_epub)

    # Write to new file
    output_path = temp_dir / "roundtrip.epub"
    writer.write(contents, output_path)

    # Read back
    new_contents = reader.read(output_path)

    # Verify contents match
    assert set(contents.files.keys()) == set(new_contents.files.keys())
    assert set(contents.binary_files.keys()) == set(new_contents.binary_files.keys())


def test_epub_writer_write_string_path(
    epub_contents: EPUBContents, temp_dir: Path
) -> None:
    """Test EPUBWriter accepts string path."""
    writer = EPUBWriter()
    output_path = temp_dir / "output.epub"

    writer.write(epub_contents, str(output_path))

    assert output_path.exists()


def test_epub_reader_read_string_path(minimal_epub: Path) -> None:
    """Test EPUBReader accepts string path."""
    reader = EPUBReader()
    contents = reader.read(str(minimal_epub))

    assert len(contents.files) > 0
