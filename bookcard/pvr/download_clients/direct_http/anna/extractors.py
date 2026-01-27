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

"""Link extraction strategies for Anna's Archive."""

import re
from typing import Protocol

from bs4 import BeautifulSoup


class LinkExtractionStrategy(Protocol):
    """Protocol for link extraction strategies."""

    def extract(self, soup: BeautifulSoup, html: str) -> str | None:
        """Extract download link from HTML."""
        ...


def is_valid_direct_link(link: str) -> bool:
    """Check if link is a valid direct download link."""
    return link.startswith(("http://", "https://")) and "/slow_download/" not in link


def _normalize_href(href: object) -> str | None:
    """Normalize BeautifulSoup href value to a single string."""
    if isinstance(href, str):
        return href
    if isinstance(href, list):
        for value in href:
            if isinstance(value, str):
                return value
    return None


class ClipboardLinkExtractor:
    """Extracts link from clipboard writeText call."""

    def extract(self, soup: BeautifulSoup, html: str) -> str | None:  # noqa: ARG002
        """Extract link using clipboard pattern."""
        match = re.search(
            r"navigator\.clipboard\.writeText\(['\"]([^'\"]+)['\"]\)", html
        )
        if match:
            link = match.group(1)
            if is_valid_direct_link(link):
                return link
        return None


class DownloadButtonExtractor:
    """Extracts link from 'Download now' button."""

    def extract(self, soup: BeautifulSoup, html: str) -> str | None:  # noqa: ARG002
        """Extract link from download button."""
        links = soup.find_all("a", href=True)
        for link in links:
            text = link.get_text(strip=True)
            if text == "📚 Download now" or "Download now" in text:
                return _normalize_href(link.get("href"))
        return None


class WindowLocationExtractor:
    """Extracts link from window.location.href assignment."""

    def extract(self, soup: BeautifulSoup, html: str) -> str | None:  # noqa: ARG002
        """Extract link using window location pattern."""
        match = re.search(r"window\.location\.href\s*=\s*['\"]([^'\"]+)['\"]", html)
        if match:
            link = match.group(1)
            if is_valid_direct_link(link):
                return link
        return None


class CopyTextExtractor:
    """Extracts link near 'copy this url' text."""

    def extract(self, soup: BeautifulSoup, html: str) -> str | None:  # noqa: ARG002
        """Extract link relative to copy text."""
        copy_text = soup.find(string=lambda s: s and "copy this url" in s.lower())
        if copy_text and copy_text.parent:
            parent = copy_text.parent
            next_link = parent.find_next("a", href=True)
            if next_link:
                href = _normalize_href(next_link.get("href"))
                if href:
                    return href
            code_elem = parent.find_next("code")
            if code_elem:
                return code_elem.get_text(strip=True)
            for sibling in parent.find_next_siblings():
                text = (
                    sibling.get_text(strip=True)
                    if hasattr(sibling, "get_text")
                    else str(sibling).strip()
                )
                if text.startswith("http"):
                    return text
        return None


class GenericLinkExtractor:
    """Extracts link from other common patterns."""

    def extract(self, soup: BeautifulSoup, html: str) -> str | None:  # noqa: ARG002
        """Extract link using generic patterns."""
        for a_tag in soup.find_all("a", href=True):
            if a_tag.has_attr("download"):
                href = _normalize_href(a_tag.get("href"))
                if href and is_valid_direct_link(href):
                    return href

        for span in soup.find_all(
            "span", class_=lambda c: c and "whitespace-normal" in c
        ):
            text = span.get_text(strip=True)
            if is_valid_direct_link(text):
                return text

        for span in soup.find_all("span", class_=lambda c: c and "bg-gray-200" in c):
            text = span.get_text(strip=True)
            if text.startswith(("http://", "https://")):
                return text
        return None


class LinkExtractor:
    """Main link extractor that delegates to strategies."""

    def __init__(self) -> None:
        self._strategies: list[LinkExtractionStrategy] = [
            ClipboardLinkExtractor(),
            DownloadButtonExtractor(),
            WindowLocationExtractor(),
            CopyTextExtractor(),
            GenericLinkExtractor(),
        ]

    def register_strategy(self, strategy: LinkExtractionStrategy) -> None:
        """Register a new extraction strategy."""
        self._strategies.append(strategy)

    def extract_link(self, soup: BeautifulSoup, html: str) -> str | None:
        """Try all strategies to extract link."""
        for strategy in self._strategies:
            if link := strategy.extract(soup, html):
                return link
        return None
