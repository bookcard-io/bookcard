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

"""Identifier extraction from Hardcover book data."""

from fundamental.metadata.providers._hardcover.utils import get_first_edition


class IdentifiersExtractor:
    """Extracts identifiers (ISBN, etc.) from book data."""

    @staticmethod
    def extract(book_data: dict) -> dict[str, str]:
        """Extract identifiers (ISBN, etc.) from book data.

        Parameters
        ----------
        book_data : dict
            Book data from API response.

        Returns
        -------
        dict[str, str]
            Dictionary of identifier type -> value.
        """
        # Try editions first (more reliable)
        edition_identifiers = IdentifiersExtractor._extract_from_editions(book_data)
        if edition_identifiers:
            return edition_identifiers

        # Fallback to isbns array if editions not available
        return IdentifiersExtractor._extract_from_isbns(book_data)

    @staticmethod
    def _extract_from_editions(book_data: dict) -> dict[str, str]:
        """Extract identifiers from editions data.

        Parameters
        ----------
        book_data : dict
            Book data from API response.

        Returns
        -------
        dict[str, str]
            Dictionary of identifier type -> value, or empty if no editions.
        """
        identifiers: dict[str, str] = {}
        edition = get_first_edition(book_data)
        if not edition:
            return identifiers

        isbn_13 = edition.get("isbn_13")
        if isbn_13:
            identifiers["isbn13"] = str(isbn_13)
        isbn_10 = edition.get("isbn_10")
        if isbn_10:
            identifiers["isbn"] = str(isbn_10)

        return identifiers

    @staticmethod
    def _extract_from_isbns(book_data: dict) -> dict[str, str]:
        """Extract identifiers from isbns array.

        Parameters
        ----------
        book_data : dict
            Book data from API response.

        Returns
        -------
        dict[str, str]
            Dictionary of identifier type -> value.
        """
        identifiers: dict[str, str] = {}
        isbns = book_data.get("isbns", [])
        if not isinstance(isbns, list):
            return identifiers

        for isbn in isbns:
            if not isbn:
                continue
            isbn_str = str(isbn).strip()
            # Determine ISBN type by length
            if len(isbn_str) == 10:
                if "isbn" not in identifiers:
                    identifiers["isbn"] = isbn_str
            elif len(isbn_str) == 13:
                if "isbn13" not in identifiers:
                    identifiers["isbn13"] = isbn_str
            elif "isbn" not in identifiers:
                identifiers["isbn"] = isbn_str

        return identifiers
