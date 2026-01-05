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

"""Download item reconciliation logic.

Handles matching client items with database items.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from bookcard.pvr.models import DownloadItem as ClientDownloadItem
from bookcard.pvr.models import ReleaseInfo
from bookcard.services.pvr.search.models import IndexerSearchResult

if TYPE_CHECKING:
    from bookcard.models.pvr import DownloadItem as DBDownloadItem
    from bookcard.services.pvr.search.matcher import DownloadItemMatcher

logger = logging.getLogger(__name__)


@dataclass
class ReconciliationResult:
    """Result of a reconciliation operation."""

    matched_pairs: list[tuple[DBDownloadItem, ClientDownloadItem]]
    unmatched_db_items: list[DBDownloadItem]
    unmatched_client_items: list[ClientDownloadItem]


class DownloadReconciler:
    """Reconciles client items with database state."""

    def __init__(self, matcher: DownloadItemMatcher) -> None:
        """Initialize reconciler.

        Parameters
        ----------
        matcher : DownloadItemMatcher
            Matcher for finding corresponding items.
        """
        self._matcher = matcher

    def reconcile(
        self,
        db_items: list[DBDownloadItem],
        client_items: list[ClientDownloadItem],
    ) -> ReconciliationResult:
        """Reconcile items and return match results.

        Parameters
        ----------
        db_items : list[DBDownloadItem]
            Existing database items.
        client_items : list[ClientDownloadItem]
            Items returned by the client.

        Returns
        -------
        ReconciliationResult
            Matched and unmatched items.
        """
        # Normalize client IDs for case-insensitive matching
        client_items_map = {
            self._normalize_id(item["client_item_id"]): item for item in client_items
        }

        matched_pairs: list[tuple[DBDownloadItem, ClientDownloadItem]] = []
        matched_client_ids = set()
        unmatched_db_items = []

        # Build lookup maps for strategies
        maps = self._matcher.build_lookup_maps(db_items)

        # First pass: Match by Client Item ID (Hash)
        for db_item in db_items:
            client_id = self._normalize_id(db_item.client_item_id)
            if client_id in client_items_map:
                matched_pairs.append((db_item, client_items_map[client_id]))
                matched_client_ids.add(client_id)
            else:
                unmatched_db_items.append(db_item)

        # Second pass: Match remaining client items to PENDING DB items
        unmatched_pending_db_items = [
            item for item in unmatched_db_items if item.client_item_id == "PENDING"
        ]

        if unmatched_pending_db_items:
            # We have pending items to match
            remaining_client_items = [
                item
                for item in client_items
                if self._normalize_id(item["client_item_id"]) not in matched_client_ids
            ]

            for client_item in remaining_client_items:
                client_id = self._normalize_id(client_item["client_item_id"])

                # Create dummy search result for matching
                result = self._create_search_result(client_item)

                # Find match in DB items
                match = self._matcher.find_match(result, maps)

                if match and match in unmatched_pending_db_items:
                    # Found a match for a pending item
                    matched_pairs.append((match, client_item))
                    matched_client_ids.add(client_id)
                    unmatched_pending_db_items.remove(match)
                    # Also remove from general unmatched list
                    if match in unmatched_db_items:
                        unmatched_db_items.remove(match)

        # Collect unmatched client items
        unmatched_client_items = [
            item
            for item in client_items
            if self._normalize_id(item["client_item_id"]) not in matched_client_ids
        ]

        return ReconciliationResult(
            matched_pairs=matched_pairs,
            unmatched_db_items=unmatched_db_items,
            unmatched_client_items=unmatched_client_items,
        )

    def _create_search_result(
        self, client_item: ClientDownloadItem
    ) -> IndexerSearchResult:
        """Create a dummy search result from a client item."""
        additional_info = {}
        if client_item.get("client_item_id"):
            additional_info["infohash"] = client_item["client_item_id"]

        if client_item.get("comment"):
            additional_info["comment"] = client_item["comment"]

        release = ReleaseInfo(
            title=client_item["title"],
            download_url="",
            size_bytes=client_item.get("size_bytes"),
            additional_info=additional_info,
        )

        return IndexerSearchResult(
            release=release,
            score=1.0,
            indexer_name="Client",
        )

    @staticmethod
    def _normalize_id(item_id: str) -> str:
        """Normalize item ID for comparison."""
        return item_id.upper()
