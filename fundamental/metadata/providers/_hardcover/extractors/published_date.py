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

"""Published date extraction from Hardcover book data."""

from fundamental.metadata.providers._hardcover.utils import get_first_edition


class PublishedDateExtractor:
    """Extracts published date from book data."""

    @staticmethod
    def extract(book_data: dict) -> str | None:
        """Extract published date from book data.

        Parameters
        ----------
        book_data : dict
            Book data from API response.

        Returns
        -------
        str | None
            Published date string or None if not available.
        """
        # Try editions first (more reliable)
        edition = get_first_edition(book_data)
        if edition:
            release_date = edition.get("release_date")
            if release_date:
                return str(release_date)

        # Fallback to top-level release_date
        release_date = book_data.get("release_date")
        if release_date:
            return str(release_date)

        # Fallback to release_year
        release_year = book_data.get("release_year")
        if release_year:
            return str(release_year)

        return None
