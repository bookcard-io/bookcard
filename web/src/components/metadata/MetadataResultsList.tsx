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

import type { MetadataRecord } from "@/hooks/useMetadataSearchStream";
import { MetadataResultItem } from "./MetadataResultItem";

export interface MetadataResultsListProps {
  results: MetadataRecord[];
  /** Callback when a metadata record is selected. */
  onSelectMetadata?: (record: MetadataRecord) => void;
}

export function MetadataResultsList({
  results,
  onSelectMetadata,
}: MetadataResultsListProps) {
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
        return (
          <MetadataResultItem
            key={`${r.source_id}:${r.external_id}:${idx}`}
            record={r}
            onSelect={onSelectMetadata}
            id={isFirstForProvider ? `result-${r.source_id}` : undefined}
          />
        );
      })}
    </div>
  );
}
