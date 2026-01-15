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

"""HTML parser for Anna's Archive search results."""

import logging
import urllib.parse
from typing import ClassVar

from bs4 import BeautifulSoup, Tag

from bookcard.pvr.indexers.annas_archive.exceptions import RowParsingError
from bookcard.pvr.indexers.annas_archive.models import AnnasArchiveTableColumns
from bookcard.pvr.models import ReleaseInfo

logger = logging.getLogger(__name__)


class FileSizeParser:
    """Parses file size strings into bytes."""

    UNIT_MULTIPLIERS: ClassVar[dict[str, int]] = {
        "b": 1,
        "kb": 1024,
        "mb": 1024**2,
        "gb": 1024**3,
        "tb": 1024**4,
    }

    @classmethod
    def parse(cls, size_str: str) -> int | None:
        """Parse '1.2 MB' into bytes."""
        try:
            parts = size_str.lower().split()
            if len(parts) != 2:
                return None
            value = float(parts[0])
            unit = parts[1]
            multiplier = cls.UNIT_MULTIPLIERS.get(unit)
            if multiplier is None:
                logger.warning("Unknown size unit: %s", unit)
                return None
            return int(value * multiplier)
        except (ValueError, IndexError) as e:
            logger.warning("Failed to parse size '%s': %s", size_str, e)
            return None


class AnnasArchiveHtmlParser:
    """Parses Anna's Archive search result HTML."""

    def parse_search_results(
        self, html_content: str, max_results: int, base_url: str
    ) -> list[ReleaseInfo]:
        """Parse HTML search results into ReleaseInfo objects."""
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

            release = self._parse_row(row, base_url)
            if release:
                releases.append(release)

        return releases

    def _parse_row(self, row: Tag, base_url: str) -> ReleaseInfo | None:
        """Parse a single table row into ReleaseInfo."""
        row_html = str(row)[:500]
        try:
            cells = row.find_all("td")
            if not self._is_valid_data_row(cells):
                return None

            return self._build_release_info(cells, base_url, row_html)

        except RowParsingError as e:
            logger.warning("Failed to parse row (field: %s): %s", e.field, e)
            return None
        except Exception:
            logger.exception("Unexpected error parsing row")
            return None

    def _build_release_info(
        self, cells: list[Tag], base_url: str, row_html: str
    ) -> ReleaseInfo:
        """Build ReleaseInfo from cells, raising RowParsingError on failure."""
        try:
            title = self._extract_title(cells)
        except Exception as e:
            msg = f"Failed to extract title: {e}"
            raise RowParsingError(msg, row_html=row_html, field="title") from e

        try:
            download_url = self._extract_download_url(cells, base_url)
        except Exception as e:
            msg = f"Failed to extract download URL: {e}"
            raise RowParsingError(msg, row_html=row_html, field="download_url") from e

        try:
            size_bytes = self._extract_size(cells)
        except Exception as e:
            msg = f"Failed to extract size: {e}"
            raise RowParsingError(msg, row_html=row_html, field="size") from e

        try:
            author = self._extract_author(cells)
        except Exception as e:
            msg = f"Failed to extract author: {e}"
            raise RowParsingError(msg, row_html=row_html, field="author") from e

        try:
            description = self._extract_description(cells)
        except Exception as e:
            msg = f"Failed to extract description: {e}"
            raise RowParsingError(msg, row_html=row_html, field="description") from e

        try:
            quality = self._extract_file_type(cells)
        except Exception as e:
            msg = f"Failed to extract file type: {e}"
            raise RowParsingError(msg, row_html=row_html, field="quality") from e

        try:
            guid = self._extract_guid(cells)
        except Exception as e:
            msg = f"Failed to extract guid: {e}"
            raise RowParsingError(msg, row_html=row_html, field="guid") from e

        return ReleaseInfo(
            title=title,
            download_url=download_url,
            size_bytes=size_bytes,
            author=author,
            category="Ebook",
            description=description,
            quality=quality,
            guid=guid,
            publish_date=None,
            indexer_id=None,
        )

    def _is_valid_data_row(self, cells: list[Tag]) -> bool:
        """Check if row contains valid data."""
        if len(cells) < AnnasArchiveTableColumns.MINIMUM_COLUMNS:
            return False

        # Must have a link in the title column
        title_cell = cells[AnnasArchiveTableColumns.TITLE]
        return title_cell.find("a") is not None

    def _extract_title(self, cells: list[Tag]) -> str:
        """Extract title from cells."""
        return cells[AnnasArchiveTableColumns.TITLE].get_text(strip=True)

    def _extract_download_url(self, cells: list[Tag], base_url: str) -> str:
        """Extract download URL from cells."""
        link_tag = cells[AnnasArchiveTableColumns.TITLE].find("a")
        relative_link = link_tag.get("href")
        return urllib.parse.urljoin(base_url, relative_link)

    def _extract_size(self, cells: list[Tag]) -> int | None:
        """Extract file size from cells."""
        size_str = cells[AnnasArchiveTableColumns.SIZE].get_text(strip=True)
        return FileSizeParser.parse(size_str)

    def _extract_author(self, cells: list[Tag]) -> str:
        """Extract author from cells."""
        return cells[AnnasArchiveTableColumns.AUTHOR].get_text(strip=True)

    def _extract_description(self, cells: list[Tag]) -> str:
        """Extract description/publisher from cells."""
        publisher = cells[AnnasArchiveTableColumns.PUBLISHER].get_text(strip=True)
        return f"Publisher: {publisher}"

    def _extract_file_type(self, cells: list[Tag]) -> str:
        """Extract file type from cells."""
        return cells[AnnasArchiveTableColumns.FILE_TYPE].get_text(strip=True).lower()

    def _extract_guid(self, cells: list[Tag]) -> str | None:
        """Extract MD5 GUID from cells."""
        link_tag = cells[AnnasArchiveTableColumns.TITLE].find("a")
        relative_link = link_tag.get("href")
        return relative_link.split("/")[-1] if relative_link else None
