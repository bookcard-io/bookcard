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

"""Language extraction from Hardcover book data."""

from fundamental.metadata.providers._hardcover.utils import get_first_edition


class LanguagesExtractor:
    """Extracts languages from book data."""

    @staticmethod
    def extract(book_data: dict) -> list[str]:
        """Extract languages from book data.

        Parameters
        ----------
        book_data : dict
            Book data from API response.

        Returns
        -------
        list[str]
            List of language codes.
        """
        languages: list[str] = []
        edition = get_first_edition(book_data)
        if edition:
            language = edition.get("language")
            if isinstance(language, dict):
                code3 = language.get("code3")
                if code3:
                    languages.append(str(code3))
        return languages
