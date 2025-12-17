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

"""Series information extraction from Hardcover book data."""


class SeriesExtractor:
    """Extracts series information from book data."""

    @staticmethod
    def extract(book_data: dict) -> tuple[str | None, float | None]:
        """Extract series information from book data.

        Parameters
        ----------
        book_data : dict
            Book data from API response.

        Returns
        -------
        tuple[str | None, float | None]
            Tuple of (series name, series index).
        """
        # Hardcover provides series_names array, but not series index
        # This would need to be extracted from title or fetched from book_series
        series_names = book_data.get("series_names", [])
        if isinstance(series_names, list) and series_names:
            return str(series_names[0]), None
        return None, None
