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

"""Tests for OpenLibrary dump parsers to achieve 100% coverage."""

from __future__ import annotations

import gzip
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from bookcard.services.tasks.openlibrary.models import DumpRecord
from bookcard.services.tasks.openlibrary.parser import (
    DumpFileParser,
    OpenLibraryDumpParser,
)


def create_gzip_dump_file(file_path: Path, lines: list[str]) -> None:
    """Create a gzipped dump file for testing.

    Parameters
    ----------
    file_path : Path
        Path to create the file.
    lines : list[str]
        Lines to write to the file.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(file_path, "wt", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


class ConcreteDumpFileParser(DumpFileParser):
    """Concrete implementation of DumpFileParser for testing."""

    def parse_line(self, line: str) -> DumpRecord | None:
        """Parse a single line from dump file.

        Parameters
        ----------
        line : str
            Line from dump file.

        Returns
        -------
        DumpRecord | None
            Parsed record or None if line is invalid.
        """
        if line.strip() == "valid":
            return DumpRecord(
                record_type="test",
                key="/test/1",
                revision=1,
                last_modified=None,
                data={},
            )
        return None


class TestDumpFileParserParseFile:
    """Test DumpFileParser.parse_file method."""

    @pytest.fixture
    def parser(self) -> ConcreteDumpFileParser:
        """Create parser instance.

        Returns
        -------
        ConcreteDumpFileParser
            Parser instance.
        """
        return ConcreteDumpFileParser()

    def test_parse_file_success(
        self, parser: ConcreteDumpFileParser, tmp_path: Path
    ) -> None:
        """Test successful file parsing.

        Parameters
        ----------
        parser : ConcreteDumpFileParser
            Parser instance.
        tmp_path : Path
            Temporary directory path.
        """
        file_path = tmp_path / "test.txt.gz"
        create_gzip_dump_file(file_path, ["valid", "invalid", "valid"])

        records = list(parser.parse_file(file_path))

        assert len(records) == 2
        assert all(isinstance(r, DumpRecord) for r in records)

    def test_parse_file_not_found(
        self, parser: ConcreteDumpFileParser, tmp_path: Path
    ) -> None:
        """Test parsing non-existent file.

        Parameters
        ----------
        parser : ConcreteDumpFileParser
            Parser instance.
        tmp_path : Path
            Temporary directory path.
        """
        file_path = tmp_path / "nonexistent.txt.gz"

        records = list(parser.parse_file(file_path))

        assert len(records) == 0

    def test_parse_file_exception(
        self, parser: ConcreteDumpFileParser, tmp_path: Path
    ) -> None:
        """Test file parsing with exception.

        Parameters
        ----------
        parser : ConcreteDumpFileParser
            Parser instance.
        tmp_path : Path
            Temporary directory path.
        """
        file_path = tmp_path / "test.txt.gz"
        create_gzip_dump_file(file_path, ["valid"])

        # Mock gzip.open to raise an exception during iteration
        with patch(
            "bookcard.services.tasks.openlibrary.parser.gzip.open"
        ) as mock_gzip_open:
            mock_file = MagicMock()
            mock_file.__enter__ = MagicMock(return_value=mock_file)
            mock_file.__exit__ = MagicMock(return_value=False)
            mock_file.__iter__ = MagicMock(side_effect=Exception("File error"))
            mock_gzip_open.return_value = mock_file

            with pytest.raises(Exception, match="File error"):
                list(parser.parse_file(file_path))


class TestOpenLibraryDumpParserParseLine:
    """Test OpenLibraryDumpParser.parse_line method."""

    @pytest.fixture
    def parser(self) -> OpenLibraryDumpParser:
        """Create parser instance.

        Returns
        -------
        OpenLibraryDumpParser
            Parser instance.
        """
        return OpenLibraryDumpParser()

    @pytest.mark.parametrize(
        ("line", "expected_type", "expected_key", "has_revision", "has_date"),
        [
            (
                'author\t/authors/OL123A\t1\t2008-04-01T00:00:00\t{"name": "Test"}',
                "author",
                "/authors/OL123A",
                True,
                True,
            ),
            (
                'work\t/works/OL456W\t2\t2009-05-15T12:30:00Z\t{"title": "Book"}',
                "work",
                "/works/OL456W",
                True,
                True,
            ),
            (
                'edition\t/editions/OL789E\t3\t2010-06-20\t{"isbn": "123"}',
                "edition",
                "/editions/OL789E",
                True,
                True,
            ),
            (
                'author\t/authors/OL999A\t\t\t{"name": "No date"}',
                "author",
                "/authors/OL999A",
                False,
                False,
            ),
            (
                'author\t/authors/OL999A\t5\t\t{"name": "No date"}',
                "author",
                "/authors/OL999A",
                True,
                False,
            ),
        ],
    )
    def test_parse_line_valid(
        self,
        parser: OpenLibraryDumpParser,
        line: str,
        expected_type: str,
        expected_key: str,
        has_revision: bool,
        has_date: bool,
    ) -> None:
        """Test parsing valid lines.

        Parameters
        ----------
        parser : OpenLibraryDumpParser
            Parser instance.
        line : str
            Line to parse.
        expected_type : str
            Expected record type.
        expected_key : str
            Expected key.
        has_revision : bool
            Whether revision should be present.
        has_date : bool
            Whether date should be present.
        """
        result = parser.parse_line(line)
        assert result is not None
        assert result.record_type == expected_type
        assert result.key == expected_key
        if has_revision:
            assert result.revision is not None
        else:
            assert result.revision is None
        if has_date:
            assert result.last_modified is not None
        else:
            assert result.last_modified is None
        assert isinstance(result.data, dict)

    @pytest.mark.parametrize(
        "line",
        [
            "invalid",
            "too\tfew\tparts",
            "author\tkey\trev\tdate",
            "author\tkey\trev\tdate\tinvalid_json{",
            "author\tkey\trev\tdate\tnot_json",
        ],
    )
    def test_parse_line_invalid(self, parser: OpenLibraryDumpParser, line: str) -> None:
        """Test parsing invalid lines.

        Parameters
        ----------
        parser : OpenLibraryDumpParser
            Parser instance.
        line : str
            Invalid line to parse.
        """
        result = parser.parse_line(line)
        assert result is None

    def test_parse_line_invalid_date_format(
        self, parser: OpenLibraryDumpParser
    ) -> None:
        """Test parsing line with invalid date format.

        Parameters
        ----------
        parser : OpenLibraryDumpParser
            Parser instance.
        """
        line = 'author\t/authors/OL1A\t1\tinvalid-date\t{"name": "Test"}'
        result = parser.parse_line(line)
        assert result is not None
        assert result.last_modified is None  # Should handle invalid date gracefully

    def test_parse_line_empty_revision(self, parser: OpenLibraryDumpParser) -> None:
        """Test parsing line with empty revision.

        Parameters
        ----------
        parser : OpenLibraryDumpParser
            Parser instance.
        """
        line = 'author\t/authors/OL1A\t\t2008-04-01T00:00:00\t{"name": "Test"}'
        result = parser.parse_line(line)
        assert result is not None
        assert result.revision is None

    def test_parse_line_empty_json(self, parser: OpenLibraryDumpParser) -> None:
        """Test parsing line with empty JSON.

        Parameters
        ----------
        parser : OpenLibraryDumpParser
            Parser instance.
        """
        line = "author\t/authors/OL1A\t1\t2008-04-01T00:00:00\t{}"
        result = parser.parse_line(line)
        assert result is not None
        assert result.data == {}


class TestOpenLibraryDumpParserParseFile:
    """Test OpenLibraryDumpParser.parse_file method."""

    @pytest.fixture
    def parser(self) -> OpenLibraryDumpParser:
        """Create parser instance.

        Returns
        -------
        OpenLibraryDumpParser
            Parser instance.
        """
        return OpenLibraryDumpParser()

    def test_parse_file_success(
        self, parser: OpenLibraryDumpParser, tmp_path: Path
    ) -> None:
        """Test successful file parsing.

        Parameters
        ----------
        parser : OpenLibraryDumpParser
            Parser instance.
        tmp_path : Path
            Temporary directory path.
        """
        file_path = tmp_path / "test.txt.gz"
        lines = [
            'author\t/authors/OL1A\t1\t2008-04-01T00:00:00\t{"name": "Author 1"}',
            'work\t/works/OL1W\t1\t2008-04-01T00:00:00\t{"title": "Work 1"}',
            "invalid",
        ]
        create_gzip_dump_file(file_path, lines)

        records = list(parser.parse_file(file_path))

        assert len(records) == 2
        assert records[0].record_type == "author"
        assert records[1].record_type == "work"

    def test_parse_file_not_found(
        self, parser: OpenLibraryDumpParser, tmp_path: Path
    ) -> None:
        """Test parsing non-existent file.

        Parameters
        ----------
        parser : OpenLibraryDumpParser
            Parser instance.
        tmp_path : Path
            Temporary directory path.
        """
        file_path = tmp_path / "nonexistent.txt.gz"

        records = list(parser.parse_file(file_path))

        assert len(records) == 0

    def test_parse_file_exception(
        self, parser: OpenLibraryDumpParser, tmp_path: Path
    ) -> None:
        """Test file parsing with exception.

        Parameters
        ----------
        parser : OpenLibraryDumpParser
            Parser instance.
        tmp_path : Path
            Temporary directory path.
        """
        file_path = tmp_path / "test.txt.gz"
        create_gzip_dump_file(
            file_path, ["author\t/authors/OL1A\t1\t2008-04-01T00:00:00\t{}"]
        )

        # Mock gzip.open to raise an exception during iteration
        with patch(
            "bookcard.services.tasks.openlibrary.parser.gzip.open"
        ) as mock_gzip_open:
            mock_file = MagicMock()
            mock_file.__enter__ = MagicMock(return_value=mock_file)
            mock_file.__exit__ = MagicMock(return_value=False)
            mock_file.__iter__ = MagicMock(side_effect=Exception("File error"))
            mock_gzip_open.return_value = mock_file

            with pytest.raises(Exception, match="File error"):
                list(parser.parse_file(file_path))
