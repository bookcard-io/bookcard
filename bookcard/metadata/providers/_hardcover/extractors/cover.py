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

"""Cover image URL extraction from Hardcover book data."""

from bookcard.metadata.providers._hardcover.utils import get_first_edition


class CoverExtractor:
    """Extracts cover image URL from book data."""

    @staticmethod
    def extract(book_data: dict) -> str | None:
        """Extract cover image URL from book data.

        Parameters
        ----------
        book_data : dict
            Book data from API response.

        Returns
        -------
        str | None
            Cover URL or None if not available.
        """
        # Try editions first (more reliable for cover images)
        edition = get_first_edition(book_data)
        if edition:
            image = edition.get("image")
            if isinstance(image, dict):
                image_url = image.get("url")
                if image_url:
                    return str(image_url)

        # Try default_cover_edition
        default_cover = book_data.get("default_cover_edition")
        if isinstance(default_cover, dict):
            cached_image = default_cover.get("cached_image")
            if isinstance(cached_image, dict):
                image_url = cached_image.get("url")
                if image_url:
                    return str(image_url)

        # Try image field if available
        image = book_data.get("image")
        if isinstance(image, dict):
            image_url = image.get("url")
            if image_url:
                return str(image_url)

        return None
