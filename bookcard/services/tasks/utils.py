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

"""Utility functions for task operations.

Provides shared utilities following Separation of Concerns.
"""

from bookcard.repositories import BookWithFullRelations


class AuthorExtractor:
    """Extracts author information from book data.

    Follows Separation of Concerns by extracting author extraction logic.
    """

    @staticmethod
    def get_primary_author_name(
        book_with_rels: BookWithFullRelations,
    ) -> str | None:
        """Extract primary author name from book relationships.

        Parameters
        ----------
        book_with_rels : BookWithFullRelations
            Book with related author data.

        Returns
        -------
        str | None
            Comma-separated author name(s) or None if no authors.
        """
        if not book_with_rels.authors:
            return None
        return ", ".join(book_with_rels.authors)
