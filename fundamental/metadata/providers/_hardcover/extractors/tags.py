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

import json


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

        # First, try cached_tags (from EDITION_QUERY)
        cached_tags = book_data.get("cached_tags")
        if cached_tags:
            parsed_cached_tags = TagsExtractor._parse_cached_tags(cached_tags)
            tags.extend(parsed_cached_tags)

        # Combine genres, moods, and tags (from search results)
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

    @staticmethod
    def _parse_cached_tags(cached_tags: str | list) -> list[str]:
        """Parse cached_tags into a list of tag names.

        Parameters
        ----------
        cached_tags : str | list
            Cached tags which may be a JSON string or list.

        Returns
        -------
        list[str]
            List of tag names.
        """
        # Handle cached_tags which may be a JSON string or list
        if isinstance(cached_tags, str):
            try:
                cached_tags = json.loads(cached_tags)
            except (json.JSONDecodeError, TypeError):
                # If it's not valid JSON, treat as single tag
                return [cached_tags] if cached_tags else []

        if not isinstance(cached_tags, list):
            return []

        # Extract tag names from cached_tags structure
        # cached_tags can be a list of tag objects with 'name' field, or just strings
        tag_names: list[str] = []
        for tag in cached_tags:
            if isinstance(tag, dict):
                # If it's a dict, try to get the name
                tag_name = tag.get("name") or tag.get("tag") or tag.get("value")
                if tag_name:
                    tag_names.append(str(tag_name))
            elif isinstance(tag, str):
                tag_names.append(tag)

        return tag_names
