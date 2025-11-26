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

"""Tags/genres extraction from Hardcover book data."""


class TagsExtractor:
    """Extracts tags/genres from book data."""

    @staticmethod
    def extract(book_data: dict) -> list[str]:
        """Extract tags/genres from book data.

        Parameters
        ----------
        book_data : dict
            Book data from API response.

        Returns
        -------
        list[str]
            List of tags/genres.
        """
        tags: list[str] = []

        # Combine genres, moods, and tags
        genres = book_data.get("genres", [])
        if isinstance(genres, list):
            tags.extend(str(genre) for genre in genres if genre)

        moods = book_data.get("moods", [])
        if isinstance(moods, list):
            tags.extend(str(mood) for mood in moods if mood)

        book_tags = book_data.get("tags", [])
        if isinstance(book_tags, list):
            tags.extend(str(tag) for tag in book_tags if tag)

        return tags
