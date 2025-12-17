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

"""Publisher extraction from Hardcover book data."""

from bookcard.metadata.providers._hardcover.utils import (
    get_first_edition,
    safe_string,
)


class PublisherExtractor:
    """Extracts publisher name from book data."""

    @staticmethod
    def extract(book_data: dict) -> str | None:
        """Extract publisher name from book data.

        Parameters
        ----------
        book_data : dict
            Book data from API response.

        Returns
        -------
        str | None
            Publisher name or None if not available.
        """
        # Try editions first
        edition = get_first_edition(book_data)
        if edition:
            publisher = edition.get("publisher")
            if isinstance(publisher, dict):
                publisher_name = publisher.get("name")
                if publisher_name:
                    return str(publisher_name)

        # Fallback to top-level publisher field
        return safe_string(book_data.get("publisher"))
