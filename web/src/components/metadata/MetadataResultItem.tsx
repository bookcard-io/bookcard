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

import { useCallback } from "react";
import { useExpandCollapseAnimation } from "@/hooks/useExpandCollapseAnimation";
import { useMetadataFieldSelection } from "@/hooks/useMetadataFieldSelection";
import type { MetadataRecord } from "@/hooks/useMetadataSearchStream";
import { createFilteredMetadataRecord } from "@/utils/createFilteredMetadataRecord";
import { MetadataFieldSelectionDrawer } from "./MetadataFieldSelectionDrawer";
import { MetadataResultHeader } from "./MetadataResultHeader";

export interface MetadataResultItemProps {
  record: MetadataRecord;
  /** Callback when this item is selected. */
  onSelect?: (record: MetadataRecord) => void;
  /** Optional ID for scrolling to this item. */
  id?: string;
  /** Whether this item is expanded. */
  isExpanded?: boolean;
  /** Callback when this item should expand/collapse. */
  onExpand?: () => void;
  /** Whether this item should be dimmed. */
  isDimmed?: boolean;
}

/**
 * Metadata result item component.
 *
 * Displays a single metadata search result with expandable field selection.
 * Follows SRP by delegating to specialized hooks and components.
 * Follows IOC via hooks and component composition.
 *
 * Parameters
 * ----------
 * props : MetadataResultItemProps
 *     Component props including record, callbacks, and state.
 */
export function MetadataResultItem({
  record,
  onSelect,
  id,
  isExpanded = false,
  onExpand,
  isDimmed = false,
}: MetadataResultItemProps) {
  const { shouldRender, isAnimatingOut, containerRef } =
    useExpandCollapseAnimation({
      isExpanded,
      animationDuration: 500,
    });

  const { selectedFields, toggleField } = useMetadataFieldSelection({
    record,
    isExpanded,
  });

  const handleCoverClick = useCallback(() => {
    onExpand?.();
  }, [onExpand]);

  const handleImport = useCallback(() => {
    const filteredRecord = createFilteredMetadataRecord(record, selectedFields);
    onSelect?.(filteredRecord);
    if (isExpanded) {
      onExpand?.();
    }
  }, [record, selectedFields, onSelect, isExpanded, onExpand]);

  const handleCancel = useCallback(() => {
    if (isExpanded) {
      onExpand?.();
    }
  }, [isExpanded, onExpand]);

  return (
    <div
      ref={containerRef}
      id={id}
      className={`flex flex-col gap-3 rounded-md border border-surface-a20 bg-surface-a10 p-3 transition-opacity ${
        isDimmed ? "opacity-50" : "opacity-100"
      }`}
    >
      <MetadataResultHeader
        record={record}
        isExpanded={isExpanded}
        onClick={handleCoverClick}
      />

      {shouldRender && (
        <MetadataFieldSelectionDrawer
          record={record}
          selectedFields={selectedFields}
          onToggleField={toggleField}
          onImport={handleImport}
          onCancel={handleCancel}
          isAnimatingOut={isAnimatingOut}
        />
      )}
    </div>
  );
}
