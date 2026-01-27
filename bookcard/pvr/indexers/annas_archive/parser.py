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
import re
import urllib.parse
from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any, ClassVar

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
        """Parse '1.2 MB' or '1.2MB' into bytes."""
        try:
            # Clean and lower
            s = size_str.lower().strip()
            # Regex to find number and unit
            match = re.match(r"^([\d.]+)\s*([a-z]+)$", s)
            if not match:
                return None

            value = float(match.group(1))
            unit = match.group(2)

            multiplier = cls.UNIT_MULTIPLIERS.get(unit)
            if multiplier is None:
                return None
            return int(value * multiplier)
        except (ValueError, IndexError):
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
        releases: list[ReleaseInfo] = []

        # Try parsing as table first
        releases.extend(self._parse_table_results(soup, max_results, base_url))

        if len(releases) < max_results:
            remaining = max_results - len(releases)
            releases.extend(self._parse_div_results(soup, remaining, base_url))

        return releases

    def _parse_table_results(
        self, soup: BeautifulSoup, max_results: int, base_url: str
    ) -> list[ReleaseInfo]:
        """Parse results from table layout."""
        releases: list[ReleaseInfo] = []
        table = soup.find("table")
        if not table:
            return []

        rows = table.find_all("tr")
        for row in rows:
            if len(releases) >= max_results:
                break
            release = self._parse_row(row, base_url)
            if release:
                releases.append(release)
        return releases

    def _parse_div_results(
        self, soup: BeautifulSoup, max_results: int, base_url: str
    ) -> list[ReleaseInfo]:
        """Parse results from div/list layout."""
        releases: list[ReleaseInfo] = []
        div_rows = soup.find_all(
            "div",
            class_=lambda c: c and "flex" in c and "border-b" in c and "pt-3" in c,
        )

        for row in div_rows:
            if len(releases) >= max_results:
                break

            # Verify it's likely a result row by checking for md5 link
            if not row.find("a", href=re.compile(r"/md5/")):
                continue

            release = self._parse_div_row(row, base_url)
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
            # Required fields
            title = self._extract_title(cells)
            download_url = self._extract_download_url(cells, base_url)
        except (AttributeError, ValueError, IndexError, TypeError) as e:
            msg = f"Failed to extract required field: {e}"
            raise RowParsingError(msg, row_html=row_html, field="required") from e

        # Optional fields
        size_bytes = self._safe_extract(self._extract_size, cells)
        author = self._safe_extract(self._extract_author, cells)
        description = self._safe_extract(self._extract_description, cells)
        quality = self._safe_extract(self._extract_file_type, cells)
        guid = self._safe_extract(self._extract_guid, cells)

        # Extract language
        language = self._extract_language(cells)

        # Extract year/publish_date
        publish_date = self._extract_publish_date(cells)

        return ReleaseInfo(
            title=title,
            download_url=download_url,
            size_bytes=size_bytes,
            author=author,
            category="Ebook",
            description=description,
            quality=quality,
            guid=guid,
            publish_date=publish_date,
            indexer_id=None,
            language=language,
        )

    def _safe_extract(
        self,
        extractor_func: Callable[..., Any],
        *args: Any,  # noqa: ANN401
    ) -> Any:  # noqa: ANN401
        """Safely extract a field, returning None on failure."""
        try:
            return extractor_func(*args)
        except (AttributeError, ValueError, IndexError, TypeError):
            return None

    def _extract_language(self, cells: list[Tag]) -> str | None:
        """Extract language from cells."""
        with suppress(AttributeError, ValueError, IndexError):
            if len(cells) > AnnasArchiveTableColumns.LANGUAGE:
                raw_lang = cells[AnnasArchiveTableColumns.LANGUAGE].get_text(strip=True)
                if raw_lang:
                    parts = [p.strip() for p in raw_lang.split(",")]
                    # Prefer non-English language if multiple are present
                    non_en = next((p for p in parts if p.lower() != "en"), None)
                    return non_en if non_en else parts[0]
        return None

    def _extract_publish_date(self, cells: list[Tag]) -> datetime | None:
        """Extract publish date from cells."""
        with suppress(AttributeError, ValueError, IndexError):
            if len(cells) > AnnasArchiveTableColumns.YEAR:
                year_str = cells[AnnasArchiveTableColumns.YEAR].get_text(strip=True)
                if re.match(r"^\d{4}$", year_str):
                    return datetime(int(year_str), 1, 1, tzinfo=UTC)
        return None

    def _parse_div_row(self, row: Tag, base_url: str) -> ReleaseInfo | None:
        """Parse a div-based result row."""
        try:
            # Title & Link
            title_link = self._find_title_link(row)
            if not title_link:
                return None

            title = title_link.get_text(strip=True)
            relative_link = title_link.get("href")
            download_url = urllib.parse.urljoin(base_url, relative_link)
            guid = relative_link.split("/")[-1] if relative_link else None  # ty:ignore[possibly-missing-attribute]

            # Author
            author_tag = row.find("a", href=re.compile(r"/search\?q="))
            author = author_tag.get_text(strip=True) if author_tag else None

            # Description
            desc_div = row.find(
                "div", class_=lambda c: c and "line-clamp" in c and "text-gray-600" in c
            )
            description = desc_div.get_text(strip=True) if desc_div else None

            # Metadata line
            metadata = self._extract_metadata(row)

            return ReleaseInfo(
                title=title,
                download_url=download_url,  # ty:ignore[invalid-argument-type]
                size_bytes=metadata["size_bytes"],
                author=author,
                category=metadata["category"],
                description=description,
                quality=metadata["quality"],
                guid=guid,
                publish_date=metadata["publish_date"],
                indexer_id=None,
                language=metadata["language"],
            )

        except (AttributeError, ValueError, TypeError, IndexError) as e:
            # Catch specific exceptions if possible, but for parsing logic, catching all
            # and logging is safer to prevent one bad row from crashing the whole search
            logger.warning("Failed to parse div row: %s", e)
            return None

    def _find_title_link(self, row: Tag) -> Tag | None:
        """Find the main title link in a div row."""
        # Look for the main title link: <a href="/md5/..." ... class="... text-lg ...">
        title_link = row.find(
            "a", class_=lambda c: c and "text-lg" in c and "font-semibold" in c
        )
        if title_link:
            return title_link

        # Fallback: find first /md5/ link that has text
        links = row.find_all("a", href=re.compile(r"^/md5/"))
        for link in links:
            if link.get_text(strip=True):
                return link
        return None

    def _extract_metadata(self, row: Tag) -> dict[str, Any]:
        """Extract metadata (language, size, etc.) from row."""
        info = {
            "language": None,
            "quality": None,
            "size_bytes": None,
            "publish_date": None,
            "category": "Ebook",
        }

        # Metadata line: <div class="text-gray-800 ... text-sm ...">
        metadata_div = row.find(
            "div",
            class_=lambda c: (
                c and "text-gray-800" in c and "text-sm" in c and "mt-2" in c
            ),
        )

        if not metadata_div:
            return info

        text = metadata_div.get_text(strip=True)
        parts = [p.strip() for p in text.split("·")]

        for part in parts:
            if re.search(r"\[[a-z]{2,3}\]$", part):
                info["language"] = part
            elif re.match(r"^\d+(\.\d+)?(KB|MB|GB|TB|B)$", part, re.IGNORECASE):
                info["size_bytes"] = FileSizeParser.parse(part)
            elif re.match(r"^\d{4}$", part):
                with suppress(ValueError):
                    year = int(part)
                    info["publish_date"] = datetime(year, 1, 1, tzinfo=UTC)
            elif part.lower() in [
                "epub",
                "pdf",
                "mobi",
                "azw3",
                "cbz",
                "cbr",
                "zip",
                "rar",
            ]:
                info["quality"] = part.lower()
            elif "Book" in part or "Article" in part or "Magazine" in part:
                info["category"] = part

        return info

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
