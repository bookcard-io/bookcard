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

"""Tests for ComicRack importer."""

from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from bookcard.services.readlist.comicrack_importer import ComicRackImporter


def test_comicrack_importer_can_import() -> None:
    """Test that importer recognizes .cbl files."""
    importer = ComicRackImporter()
    assert importer.can_import(Path("test.cbl")) is True
    assert importer.can_import(Path("test.CBL")) is True
    assert importer.can_import(Path("test.xml")) is False
    assert importer.can_import(Path("test.txt")) is False


def test_comicrack_importer_parse_valid_file() -> None:
    """Test parsing a valid .cbl file."""
    importer = ComicRackImporter()
    xml_content = """<?xml version="1.0"?>
<ReadingList>
    <Name>Test List</Name>
    <Description>Test Description</Description>
    <Books>
        <Book>
            <Series>Test Series</Series>
            <Volume>1</Volume>
            <Number>1</Number>
            <Year>2020</Year>
            <Title>Test Book</Title>
            <Writer>Test Author</Writer>
        </Book>
    </Books>
</ReadingList>"""

    with NamedTemporaryFile(mode="w", suffix=".cbl", delete=False) as f:
        f.write(xml_content)
        f.flush()
        file_path = Path(f.name)

    try:
        result = importer.parse(file_path)
        assert result.name == "Test List"
        assert result.description == "Test Description"
        assert len(result.books) == 1
        assert result.books[0].series == "Test Series"
        assert result.books[0].volume == 1.0
        assert result.books[0].issue == 1.0
        assert result.books[0].year == 2020
        assert result.books[0].title == "Test Book"
        assert result.books[0].author == "Test Author"
    finally:
        file_path.unlink()


def test_comicrack_importer_parse_invalid_file() -> None:
    """Test parsing an invalid .cbl file."""
    importer = ComicRackImporter()
    xml_content = "<?xml version='1.0'?><InvalidRoot></InvalidRoot>"

    with NamedTemporaryFile(mode="w", suffix=".cbl", delete=False) as f:
        f.write(xml_content)
        f.flush()
        file_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match=r"Invalid \.cbl file"):
            importer.parse(file_path)
    finally:
        file_path.unlink()


def test_comicrack_importer_get_format_name() -> None:
    """Test format name."""
    importer = ComicRackImporter()
    assert importer.get_format_name() == "ComicRack .cbl"
