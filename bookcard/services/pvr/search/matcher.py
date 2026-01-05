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

"""Matchers for search results to download items."""

import re
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

from bookcard.models.pvr import DownloadItem
from bookcard.services.pvr.search.models import IndexerSearchResult


@dataclass
class DownloadItemMaps:
    """Lookup maps for download items."""

    url_map: dict[str, DownloadItem]
    guid_map: dict[str, DownloadItem]
    infohash_map: dict[str, DownloadItem]
    meta_map: dict[tuple[int, str, int], DownloadItem]
    title_map: dict[str, DownloadItem]


class DownloadItemMatchStrategy(ABC):
    """Strategy for matching search results to download items."""

    @abstractmethod
    def match(
        self, result: IndexerSearchResult, maps: DownloadItemMaps
    ) -> DownloadItem | None:
        """Match result to download item.

        Parameters
        ----------
        result : IndexerSearchResult
            Search result to match.
        maps : DownloadItemMaps
            Lookup maps of existing download items.

        Returns
        -------
        DownloadItem | None
            Matching download item if found, None otherwise.
        """


class GuidMatchStrategy(DownloadItemMatchStrategy):
    """Match by GUID."""

    def match(
        self, result: IndexerSearchResult, maps: DownloadItemMaps
    ) -> DownloadItem | None:
        """Match result to download item by GUID.

        Parameters
        ----------
        result : IndexerSearchResult
            Search result to match.
        maps : DownloadItemMaps
            Lookup maps of existing download items.

        Returns
        -------
        DownloadItem | None
            Matching download item if found, None otherwise.
        """
        if result.release.guid:
            return maps.guid_map.get(result.release.guid)
        return None


class InfohashMatchStrategy(DownloadItemMatchStrategy):
    """Match by Infohash."""

    def match(
        self, result: IndexerSearchResult, maps: DownloadItemMaps
    ) -> DownloadItem | None:
        """Match result to download item by Infohash.

        Parameters
        ----------
        result : IndexerSearchResult
            Search result to match.
        maps : DownloadItemMaps
            Lookup maps of existing download items.

        Returns
        -------
        DownloadItem | None
            Matching download item if found, None otherwise.
        """
        if result.release.additional_info:
            infohash = str(result.release.additional_info.get("infohash"))
            # Ensure infohash is valid string and not "None"
            if infohash and infohash != "None":
                return maps.infohash_map.get(infohash)
        return None


class UrlMatchStrategy(DownloadItemMatchStrategy):
    """Match by Download URL."""

    def match(
        self, result: IndexerSearchResult, maps: DownloadItemMaps
    ) -> DownloadItem | None:
        """Match result to download item by Download URL.

        Parameters
        ----------
        result : IndexerSearchResult
            Search result to match.
        maps : DownloadItemMaps
            Lookup maps of existing download items.

        Returns
        -------
        DownloadItem | None
            Matching download item if found, None otherwise.
        """
        return maps.url_map.get(result.release.download_url)


class CommentMatchStrategy(DownloadItemMatchStrategy):
    """Match by Comment (MID extraction)."""

    def match(
        self, result: IndexerSearchResult, maps: DownloadItemMaps
    ) -> DownloadItem | None:
        """Match result to download item by Comment.

        Extracts MID from comment (MID=...) and matches against GUID.

        Parameters
        ----------
        result : IndexerSearchResult
            Search result to match.
        maps : DownloadItemMaps
            Lookup maps of existing download items.

        Returns
        -------
        DownloadItem | None
            Matching download item if found, None otherwise.
        """
        if not result.release.additional_info:
            return None

        comment = result.release.additional_info.get("comment")
        if not comment or not isinstance(comment, str):
            return None

        match = re.search(r"MID=(\d+)", comment)
        if not match:
            return None

        mid = match.group(1)

        # Iterate guid_map to find match
        # Since we don't have a map for mid -> item, we have to iterate
        for guid, item in maps.guid_map.items():
            if mid in guid:
                return item

        return None


class MetaMatchStrategy(DownloadItemMatchStrategy):
    """Match by Metadata (Indexer ID, Title, Size)."""

    def match(
        self, result: IndexerSearchResult, maps: DownloadItemMaps
    ) -> DownloadItem | None:
        """Match result to download item by Metadata (Indexer ID, Title, Size).

        Parameters
        ----------
        result : IndexerSearchResult
            Search result to match.
        maps : DownloadItemMaps
            Lookup maps of existing download items.

        Returns
        -------
        DownloadItem | None
            Matching download item if found, None otherwise.
        """
        if (
            result.release.indexer_id is not None
            and result.release.title
            and result.release.size_bytes is not None
        ):
            key = (
                result.release.indexer_id,
                result.release.title,
                result.release.size_bytes,
            )
            return maps.meta_map.get(key)
        return None


class TitleMatchStrategy(DownloadItemMatchStrategy):
    """Match by Title."""

    def match(
        self, result: IndexerSearchResult, maps: DownloadItemMaps
    ) -> DownloadItem | None:
        """Match result to download item by Title.

        Parameters
        ----------
        result : IndexerSearchResult
            Search result to match.
        maps : DownloadItemMaps
            Lookup maps of existing download items.

        Returns
        -------
        DownloadItem | None
            Matching download item if found, None otherwise.
        """
        if result.release.title:
            return maps.title_map.get(result.release.title)
        return None


class DownloadItemMatcher:
    """Matches search results to existing download items."""

    def __init__(
        self, strategies: list[DownloadItemMatchStrategy] | None = None
    ) -> None:
        """Initialize matcher.

        Parameters
        ----------
        strategies : list[DownloadItemMatchStrategy] | None
            List of matching strategies. If None, default strategies are used.
        """
        self._strategies = strategies or [
            GuidMatchStrategy(),
            InfohashMatchStrategy(),
            UrlMatchStrategy(),
            CommentMatchStrategy(),
            MetaMatchStrategy(),
        ]

    def build_lookup_maps(self, items: Sequence[DownloadItem]) -> DownloadItemMaps:
        """Build lookup maps for download items.

        Parameters
        ----------
        items : Sequence[DownloadItem]
            List of download items.

        Returns
        -------
        DownloadItemMaps
            Object containing lookup maps.
        """
        url_map: dict[str, DownloadItem] = {}
        guid_map: dict[str, DownloadItem] = {}
        infohash_map: dict[str, DownloadItem] = {}
        meta_map: dict[tuple[int, str, int], DownloadItem] = {}
        title_map: dict[str, DownloadItem] = {}

        for item in sorted(items, key=lambda x: x.created_at):
            if item.download_url:
                url_map[item.download_url] = item

            if item.guid:
                guid_map[item.guid] = item

            if item.release_info and isinstance(item.release_info, dict):
                self._update_maps_from_release_info(item, guid_map, infohash_map)

            if (
                item.indexer_id is not None
                and item.title
                and item.size_bytes is not None
            ):
                key = (item.indexer_id, item.title, item.size_bytes)
                meta_map[key] = item

            if item.title:
                title_map[item.title] = item

        return DownloadItemMaps(
            url_map=url_map,
            guid_map=guid_map,
            infohash_map=infohash_map,
            meta_map=meta_map,
            title_map=title_map,
        )

    def _update_maps_from_release_info(
        self,
        item: DownloadItem,
        guid_map: dict[str, DownloadItem],
        infohash_map: dict[str, DownloadItem],
    ) -> None:
        """Update maps from release info.

        Parameters
        ----------
        item : DownloadItem
            Download item.
        guid_map : dict[str, DownloadItem]
            GUID map.
        infohash_map : dict[str, DownloadItem]
            Infohash map.
        """
        if not item.release_info:
            return

        if not item.guid:
            guid = item.release_info.get("guid")
            if guid:
                guid_map[guid] = item

        additional_info = item.release_info.get("additional_info")
        if isinstance(additional_info, dict):
            infohash = additional_info.get("infohash")
            if infohash:
                infohash_map[str(infohash)] = item

    def find_match(
        self, result: IndexerSearchResult, maps: DownloadItemMaps
    ) -> DownloadItem | None:
        """Find matching download item for a search result.

        Parameters
        ----------
        result : IndexerSearchResult
            Search result to match.
        maps : DownloadItemMaps
            Lookup maps of existing download items.

        Returns
        -------
        DownloadItem | None
            Matching download item if found, None otherwise.
        """
        for strategy in self._strategies:
            if match := strategy.match(result, maps):
                return match
        return None
