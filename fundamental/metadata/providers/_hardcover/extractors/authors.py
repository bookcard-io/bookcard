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

"""Author extraction from Hardcover book data."""


class AuthorsExtractor:
    """Extracts author names from book data."""

    @staticmethod
    def extract(book_data: dict) -> list[str]:
        """Extract author names from book data.

        Parameters
        ----------
        book_data : dict
            Book data from API response.

        Returns
        -------
        list[str]
            List of author names.
        """
        authors: list[str] = []

        # Try contributions first (more detailed)
        contributions = book_data.get("contributions", [])
        if isinstance(contributions, list):
            for contribution in contributions:
                author = contribution.get("author", {})
                if isinstance(author, dict):
                    author_name = author.get("name")
                    if author_name and author_name not in authors:
                        authors.append(str(author_name))

        # Fallback to author_names if contributions not available
        if not authors:
            author_names = book_data.get("author_names", [])
            if isinstance(author_names, list):
                authors = [str(name) for name in author_names if name]

        return authors
