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

"""SRU query builder for DNB provider.

This module handles building SRU (Search/Retrieve via URL) queries
for the DNB SRU API, following Single Responsibility Principle.
"""

from __future__ import annotations

import re


class SRUQueryBuilder:
    """Builder for SRU query strings.

    This class is responsible solely for constructing SRU query strings
    from various input parameters, with support for fuzzy matching and
    filtering non-book materials.

    Attributes
    ----------
    FILTER_NON_BOOKS : str
        SRU filter to exclude non-book materials.
    """

    FILTER_NON_BOOKS = " NOT (mat=film OR mat=music OR mat=microfiches OR cod=tt)"

    def build_queries(
        self,
        idn: str | None = None,
        isbn: str | None = None,
        title: str | None = None,
    ) -> list[str]:
        """Build SRU query variations from input parameters.

        Creates multiple query variations with increasing fuzziness
        to improve search results. Filters out non-book materials.

        Parameters
        ----------
        idn : str | None
            DNB IDN identifier.
        isbn : str | None
            ISBN identifier.
        title : str | None
            Book title for search.

        Returns
        -------
        list[str]
            List of SRU query strings, ordered by specificity.
        """
        queries: list[str] = []

        # Direct identifier queries (most specific)
        if idn:
            queries.append(f"num={idn}")
        elif isbn:
            queries.append(f"num={isbn}")
        elif title:
            # Title-based queries with fuzzy matching
            queries.extend(self._build_title_queries(title))

        # Apply filters to exclude non-book materials
        return [q + self.FILTER_NON_BOOKS for q in queries]

    def _build_title_queries(self, title: str) -> list[str]:
        """Build title-based SRU queries with fuzzy matching.

        Creates query variations:
        1. Exact title match (preserving spaces)
        2. Title with German joiners removed (fuzzy match)

        Parameters
        ----------
        title : str
            Book title.

        Returns
        -------
        list[str]
            List of title query strings.
        """
        queries: list[str] = []

        # Basic title search - preserve spaces
        title_tokens = self._tokenize_title(title, strip_joiners=False)
        if title_tokens:
            query_title = " ".join(title_tokens)
            queries.append(f'tit="{query_title}"')

        # German joiner removal for fuzzy matching
        german_tokens = self._strip_german_joiners(
            self._tokenize_title(title, strip_joiners=True),
        )
        if german_tokens and german_tokens != title_tokens:
            query_title = " ".join(german_tokens)
            queries.append(f'tit="{query_title}"')

        return queries

    def _tokenize_title(self, title: str, strip_joiners: bool = False) -> list[str]:
        """Tokenize title into words.

        Parameters
        ----------
        title : str
            Book title.
        strip_joiners : bool
            Whether to strip common joiners.

        Returns
        -------
        list[str]
            List of title tokens.
        """
        # Simple tokenization - split on whitespace and punctuation
        tokens = re.findall(r"\b\w+\b", title)
        if strip_joiners:
            tokens = self._strip_german_joiners(tokens)
        return tokens

    def _strip_german_joiners(self, wordlist: list[str]) -> list[str]:
        """Remove German joiners from word list.

        Parameters
        ----------
        wordlist : list[str]
            List of words.

        Returns
        -------
        list[str]
            List with German joiners removed.
        """
        german_joiners = {
            "ein",
            "eine",
            "einer",
            "der",
            "die",
            "das",
            "und",
            "oder",
        }
        return [word for word in wordlist if word.lower() not in german_joiners]
