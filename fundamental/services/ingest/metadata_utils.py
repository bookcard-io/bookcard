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

"""String normalization and similarity utilities for metadata processing.

Follows SoC by separating string manipulation utilities from business logic.
"""

from difflib import SequenceMatcher


class StringNormalizer:
    """String normalization utilities for metadata comparison.

    Provides consistent normalization for ISBNs, names, and name lists.
    """

    @staticmethod
    def normalize_isbn(isbn: str) -> str:
        """Normalize ISBN for comparison.

        Removes non-alphanumeric characters and converts to lowercase.

        Parameters
        ----------
        isbn : str
            ISBN string to normalize.

        Returns
        -------
        str
            Normalized ISBN.
        """
        return "".join(c for c in isbn if c.isalnum()).lower()

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize a name for comparison.

        Strips whitespace and converts to lowercase.

        Parameters
        ----------
        name : str
            Name string to normalize.

        Returns
        -------
        str
            Normalized name.
        """
        return name.strip().lower()

    @staticmethod
    def normalize_name_set(names: list[str]) -> set[str]:
        """Normalize a list of names to a set.

        Strips whitespace, converts to lowercase, and filters empty strings.

        Parameters
        ----------
        names : list[str]
            List of name strings.

        Returns
        -------
        set[str]
            Set of normalized names.
        """
        return {StringNormalizer.normalize_name(n) for n in names if n.strip()}


class StringSimilarityCalculator:
    """Calculates similarity between strings.

    Uses SequenceMatcher for accurate similarity calculation.
    """

    @staticmethod
    def similarity(str1: str, str2: str) -> float:
        """Calculate similarity between two strings.

        Uses SequenceMatcher ratio for accurate similarity calculation.
        Returns 0.0 for empty strings.

        Parameters
        ----------
        str1 : str
            First string.
        str2 : str
            Second string.

        Returns
        -------
        float
            Similarity score (0.0-1.0).
        """
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1, str2).ratio()

    @staticmethod
    def authors_match(query_authors: list[str], record_authors: list[str]) -> bool:
        """Check if author lists match.

        Normalizes both lists and checks for any overlap.

        Parameters
        ----------
        query_authors : list[str]
            Query author list.
        record_authors : list[str]
            Record author list.

        Returns
        -------
        bool
            True if there's any overlap, False otherwise.
        """
        if not query_authors or not record_authors:
            return False

        norm_query = StringNormalizer.normalize_name_set(query_authors)
        norm_record = StringNormalizer.normalize_name_set(record_authors)

        return bool(norm_query & norm_record)
