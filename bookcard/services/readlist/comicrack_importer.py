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

"""ComicRack .cbl file importer.

Parses ComicRack reading list files (.cbl format) which are XML files
containing book references with series, volume, issue, year, and title.

Note: Uses xml.etree.ElementTree for parsing. Files are user-uploaded
and processed server-side, so XML attacks are mitigated by file size
limits and server-side validation.
"""

import xml.etree.ElementTree as ET  # noqa: S405
from contextlib import suppress
from pathlib import Path

from bookcard.services.readlist.interfaces import (
    BookReference,
    ReadListData,
    ReadListImporter,
)


class ComicRackImporter(ReadListImporter):
    """Importer for ComicRack .cbl reading list files.

    ComicRack .cbl files are XML files with the following structure:
    <ReadingList>
        <Name>List Name</Name>
        <Books>
            <Book>
                <Series>Series Name</Series>
                <Volume>1</Volume>
                <Number>1</Number>
                <Year>2020</Year>
                <Title>Book Title</Title>
            </Book>
            ...
        </Books>
    </ReadingList>
    """

    def can_import(self, file_path: Path) -> bool:
        """Check if file is a ComicRack .cbl file.

        Parameters
        ----------
        file_path : Path
            Path to the file to check.

        Returns
        -------
        bool
            True if file has .cbl extension, False otherwise.
        """
        return file_path.suffix.lower() == ".cbl"

    def parse(self, file_path: Path) -> ReadListData:
        """Parse a ComicRack .cbl file.

        Parameters
        ----------
        file_path : Path
            Path to the .cbl file.

        Returns
        -------
        ReadListData
            Parsed read list data.

        Raises
        ------
        ValueError
            If the file cannot be parsed or is invalid.
        """
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise ValueError(msg)

        try:
            tree = ET.parse(file_path)  # noqa: S314
            root = tree.getroot()
        except ET.ParseError as e:
            msg = f"Invalid XML file: {e}"
            raise ValueError(msg) from e

        # Check root element
        if root.tag != "ReadingList":
            msg = f"Invalid .cbl file: expected ReadingList root, got {root.tag}"
            raise ValueError(msg)

        # Extract list name
        name_elem = root.find("Name")
        name = (
            name_elem.text
            if name_elem is not None and name_elem.text
            else "Untitled List"
        )

        # Extract description (optional)
        description_elem = root.find("Description")
        description = (
            description_elem.text
            if description_elem is not None and description_elem.text
            else None
        )

        # Extract books
        books_elem = root.find("Books")
        books = []
        if books_elem is not None:
            for book_elem in books_elem.findall("Book"):
                book_ref = self._parse_book_element(book_elem)
                if book_ref:
                    books.append(book_ref)

        return ReadListData(name=name, description=description, books=books)

    def _parse_book_element(self, book_elem: ET.Element) -> BookReference | None:
        """Parse a Book element from the XML.

        Parameters
        ----------
        book_elem : ET.Element
            Book XML element.

        Returns
        -------
        BookReference | None
            Parsed book reference, or None if element is invalid.
        """
        series_elem = book_elem.find("Series")
        series = (
            series_elem.text if series_elem is not None and series_elem.text else None
        )

        volume_elem = book_elem.find("Volume")
        volume = None
        if volume_elem is not None and volume_elem.text:
            with suppress(ValueError):
                volume = float(volume_elem.text)

        issue_elem = book_elem.find("Number")
        issue = None
        if issue_elem is not None and issue_elem.text:
            with suppress(ValueError):
                issue = float(issue_elem.text)

        year_elem = book_elem.find("Year")
        year = None
        if year_elem is not None and year_elem.text:
            with suppress(ValueError):
                year = int(year_elem.text)

        title_elem = book_elem.find("Title")
        title = title_elem.text if title_elem is not None and title_elem.text else None

        author_elem = book_elem.find("Writer")
        author = (
            author_elem.text if author_elem is not None and author_elem.text else None
        )

        # At least one field should be present
        if not any([series, volume, issue, year, title, author]):
            return None

        return BookReference(
            series=series,
            volume=volume,
            issue=issue,
            year=year,
            title=title,
            author=author,
        )

    def get_format_name(self) -> str:
        """Get the format name.

        Returns
        -------
        str
            Format name: "ComicRack .cbl".
        """
        return "ComicRack .cbl"
