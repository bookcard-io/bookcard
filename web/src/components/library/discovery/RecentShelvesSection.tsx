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

import { useCallback, useMemo } from "react";
import { ShelfCard } from "@/components/shelves/ShelfCard";
import { useSelectedShelf } from "@/contexts/SelectedShelfContext";
import { useShelvesContext } from "@/contexts/ShelvesContext";
import { useShelfSelection } from "@/hooks/useShelfSelection";

/**
 * Recent shelves section for discovery tab.
 *
 * Displays top 5 shelves by creation date, horizontally scrollable.
 * Follows SRP by focusing solely on recent shelves display.
 */
export function RecentShelvesSection() {
  const { shelves, isLoading } = useShelvesContext();
  const { setSelectedShelfId } = useSelectedShelf();
  const { isShelfSelected, handleShelfSelect } = useShelfSelection({});

  // Sort by created_at descending and take top 5
  const recentShelves = useMemo(() => {
    return [...shelves]
      .sort((a, b) => {
        const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
        const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
        return dateB - dateA;
      })
      .slice(0, 5);
  }, [shelves]);

  const handleShelfClick = useCallback(
    (shelfId: number) => {
      setSelectedShelfId(shelfId);
      // Note: Navigation to library tab should be handled by parent
    },
    [setSelectedShelfId],
  );

  if (isLoading || recentShelves.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="m-0 font-bold text-[var(--color-text-a0)] text-xl">
        Recent Shelves
      </h2>
      <div
        className="flex gap-4 overflow-x-auto pb-2"
        style={{ scrollbarWidth: "thin" }}
      >
        {recentShelves.map((shelf) => (
          <div
            key={shelf.id}
            className="flex-shrink-0"
            style={{ width: "200px" }}
          >
            <ShelfCard
              shelf={shelf}
              allShelves={recentShelves}
              selected={isShelfSelected(shelf.id)}
              onShelfSelect={handleShelfSelect}
              onShelfClick={handleShelfClick}
              selectedShelfIds={new Set()}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
