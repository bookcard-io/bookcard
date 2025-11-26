// Copyright (C) 2025 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

"use client";

import { useEffect, useRef } from "react";
import { useMetadataResultsListState } from "@/hooks/useMetadataResultsListState";
import type { MetadataRecord } from "@/hooks/useMetadataSearchStream";
import { MetadataResultItem } from "./MetadataResultItem";

export interface MetadataResultsListProps {
  results: MetadataRecord[];
  /** Callback when a metadata record is selected. */
  onSelectMetadata?: (record: MetadataRecord) => void;
}

/**
 * List component for metadata search results.
 *
 * Manages list-level state and renders result items.
 * Follows SRP by focusing solely on list orchestration.
 * Follows IOC via hooks for state management.
 *
 * Parameters
 * ----------
 * props : MetadataResultsListProps
 *     Component props including results and selection callback.
 */
export function MetadataResultsList({
  results,
  onSelectMetadata,
}: MetadataResultsListProps) {
  const { handleExpand, isExpanded, isDimmed, expandedKey } =
    useMetadataResultsListState();

  const prevExpandedKeyRef = useRef<string | null>(null);

  useEffect(() => {
    prevExpandedKeyRef.current = expandedKey;
  }, [expandedKey]);

  if (!results || results.length === 0) {
    return null;
  }

  // Track first occurrence of each source_id to add IDs for scrolling
  const seenSourceIds = new Set<string>();

  return (
    <div className="mt-2 flex flex-col gap-3">
      {results.map((r, idx) => {
        const isFirstForProvider = !seenSourceIds.has(r.source_id);
        if (isFirstForProvider) {
          seenSourceIds.add(r.source_id);
        }
        const itemKey = `${r.source_id}:${r.external_id}:${idx}`;

        // Calculate scroll delay: if we are expanding an item that is BELOW the previously expanded item,
        // we should wait for the previous item to collapse (500ms) before scrolling to the new one.
        // This prevents the scroll position from jumping incorrectly due to layout shifts.
        let scrollDelay = 0;
        if (
          isExpanded(itemKey) &&
          prevExpandedKeyRef.current !== null &&
          prevExpandedKeyRef.current !== itemKey
        ) {
          const prevIdxStr = prevExpandedKeyRef.current.split(":").pop();
          if (prevIdxStr) {
            const prevIdx = Number.parseInt(prevIdxStr, 10);
            if (!Number.isNaN(prevIdx) && idx > prevIdx) {
              scrollDelay = 510;
            }
          }
        }

        return (
          <MetadataResultItem
            key={itemKey}
            record={r}
            onSelect={onSelectMetadata}
            id={isFirstForProvider ? `result-${r.source_id}` : undefined}
            isExpanded={isExpanded(itemKey)}
            onExpand={() => handleExpand(itemKey)}
            isDimmed={isDimmed(itemKey)}
            scrollOnCollapse={expandedKey === null}
            scrollDelay={scrollDelay}
          />
        );
      })}
    </div>
  );
}
