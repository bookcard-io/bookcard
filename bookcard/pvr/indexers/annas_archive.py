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

"""Anna's Archive indexer implementation.

This indexer scrapes the Anna's Archive website to find books.
It parses the HTML search results and returns ReleaseInfo objects.
The download URL points to the Anna's Archive MD5 details page.
"""

import logging
import urllib.parse
from collections.abc import Sequence

import httpx
from bs4 import BeautifulSoup

from bookcard.pvr.base import BaseIndexer, IndexerSettings
from bookcard.pvr.exceptions import (
    PVRProviderNetworkError,
)
from bookcard.pvr.models import ReleaseInfo

logger = logging.getLogger(__name__)


class AnnasArchiveSettings(IndexerSettings):
    """Settings for Anna's Archive indexer.

    Attributes
    ----------
    base_url : str
        Base URL of the indexer (default: "https://annas-archive.org").
    """

    base_url: str = "https://annas-archive.org"


class AnnasArchiveIndexer(BaseIndexer):
    """Indexer for Anna's Archive (Scraper)."""

    def __init__(self, settings: AnnasArchiveSettings | IndexerSettings) -> None:
        """Initialize Anna's Archive indexer.

        Parameters
        ----------
        settings : AnnasArchiveSettings | IndexerSettings
            Indexer settings.
        """
        if isinstance(settings, IndexerSettings) and not isinstance(
            settings, AnnasArchiveSettings
        ):
            # Convert generic settings to specific settings
            aa_settings = AnnasArchiveSettings(
                base_url=settings.base_url or "https://annas-archive.li",
                api_key=settings.api_key,
                timeout_seconds=settings.timeout_seconds,
                retry_count=settings.retry_count,
                categories=settings.categories,
            )
            settings = aa_settings

        super().__init__(settings)
        self.settings: AnnasArchiveSettings = settings  # type: ignore[assignment]

    def search(
        self,
        query: str,
        title: str | None = None,
        author: str | None = None,
        isbn: str | None = None,
        max_results: int = 100,
    ) -> Sequence[ReleaseInfo]:
        """Search for releases matching the query.

        Parameters
        ----------
        query : str
            General search query.
        title : str | None
            Specific title to search for.
        author : str | None
            Specific author to search for.
        isbn : str | None
            ISBN to search for.
        max_results : int
            Maximum number of results to return.

        Returns
        -------
        Sequence[ReleaseInfo]
            List of release information.
        """
        # 1. Build Query
        # Priority: ISBN > Title + Author > General Query
        search_term = ""
        if isbn:
            search_term = isbn
        elif title and author:
            search_term = f"{title} {author}"
        elif title:
            search_term = title
        else:
            search_term = query

        if not search_term:
            return []

        # 2. Construct Search URL
        params = {
            "q": search_term,
            "index": "",  # Search all shadow libraries
            "page": "1",
            "display": "table",  # Important for easier parsing
            "sort": "relevance",
        }

        url = f"{self.settings.base_url}/search"

        try:
            response = self._make_request(url, params)
            return self._parse_results(response.text, max_results)
        except Exception:
            logger.exception("Search failed for %s", search_term)
            raise

    def _parse_results(self, html_content: str, max_results: int) -> list[ReleaseInfo]:
        """Parse HTML search results into ReleaseInfo objects."""
        # Check for "No files found"
        if "No files found" in html_content:
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        table = soup.find("table")
        if not table:
            return []

        releases: list[ReleaseInfo] = []
        rows = table.find_all("tr")

        for row in rows:
            if len(releases) >= max_results:
                break

            try:
                # Basic validation to skip header/ad rows
                if not row.find("td"):
                    continue

                cells = row.find_all("td")
                if len(cells) < 10:
                    continue

                # Extract Link (The "Title" is usually in the second cell)
                link_tag = cells[1].find("a")
                if not link_tag:
                    continue

                relative_link = link_tag.get("href")
                # Clean up /md5/ prefix to get ID
                md5_id = relative_link.split("/")[-1] if relative_link else None

                # Full details URL (This becomes our "download_url" for now)
                details_url = urllib.parse.urljoin(
                    self.settings.base_url, relative_link
                )

                # Extract Metadata
                title_text = cells[1].get_text(strip=True)
                author_text = cells[2].get_text(strip=True)
                publisher_text = cells[3].get_text(strip=True)
                file_type = cells[9].get_text(strip=True).lower()
                size_str = cells[10].get_text(strip=True)

                # Parse Size
                size_bytes = self._parse_size(size_str)

                release = ReleaseInfo(
                    title=title_text,
                    download_url=details_url,  # Points to AA details page
                    size_bytes=size_bytes,
                    publish_date=None,
                    author=author_text,
                    category="Ebook",
                    description=f"Publisher: {publisher_text}",
                    quality=file_type,  # e.g. "epub", "pdf"
                    guid=md5_id,  # Use MD5 as unique ID
                    indexer_id=None,  # Will be set by service
                )
                releases.append(release)

            except (AttributeError, IndexError, ValueError, TypeError) as e:
                logger.warning("Failed to parse row: %s", e)
                continue

        return releases

    def _make_request(self, url: str, params: dict) -> httpx.Response:
        """Make HTTP request to Anna's Archive."""
        timeout = self.settings.timeout_seconds
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                return response
        except httpx.HTTPError as e:
            msg = f"HTTP Error: {e}"
            raise PVRProviderNetworkError(msg) from e

    def _parse_size(self, size_str: str) -> int | None:
        """Parse '1.2 MB' into bytes."""
        try:
            parts = size_str.lower().split()
            if len(parts) != 2:
                return None
            value = float(parts[0])
            unit = parts[1]
            multipliers = {"kb": 1024, "mb": 1024**2, "gb": 1024**3}
            return int(value * multipliers.get(unit, 1))
        except (ValueError, IndexError):
            return None

    def test_connection(self) -> bool:
        """Test connectivity to Anna's Archive."""
        try:
            # Simple check to see if the site is up
            self._make_request(self.settings.base_url, {})
        except (httpx.HTTPError, PVRProviderNetworkError):
            return False
        else:
            return True
