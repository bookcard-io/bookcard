# Copyright (C) 2026 knguyen and others
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

"""Builders for Anna's Archive indexer components."""

from bookcard.pvr.indexers.annas_archive.models import SearchParameters


class SearchQueryBuilder:
    """Builds search queries with priority logic."""

    def build(
        self,
        query: str | None = None,
        title: str | None = None,
        author: str | None = None,
        isbn: str | None = None,
    ) -> str:
        """Build search term with priority: title+author > title > query > isbn."""
        if title and author:
            return f"{title} {author}"
        if title:
            return title
        if query:
            return query
        if isbn:
            return isbn
        return ""


class SearchParametersBuilder:
    """Builds search parameters for requests."""

    def build(
        self,
        search_term: str,
        page: int = 1,
        index: str = "",
        display: str = "table",
        sort: str = "relevance",
    ) -> SearchParameters:
        """Build search parameters."""
        return SearchParameters(
            query=search_term, index=index, page=page, display=display, sort=sort
        )


class AnnasArchiveUrlBuilder:
    """Builds URLs for Anna's Archive endpoints."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def search_url(self) -> str:
        """Get search endpoint URL."""
        return f"{self.base_url}/search"
