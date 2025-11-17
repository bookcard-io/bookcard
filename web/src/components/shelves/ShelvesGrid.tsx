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

import { useEffect, useMemo, useRef, useState } from "react";
import { CreateShelfCard } from "@/components/shelves/CreateShelfCard";
import { ShelfCard } from "@/components/shelves/ShelfCard";
import { ShelfEditModal } from "@/components/shelves/ShelfEditModal";
import { useShelvesContext } from "@/contexts/ShelvesContext";
import { useUser } from "@/contexts/UserContext";
import { useShelfDataUpdates } from "@/hooks/useShelfDataUpdates";
import { useShelfGridOperations } from "@/hooks/useShelfGridOperations";
import { useShelfSelection } from "@/hooks/useShelfSelection";
import type { Shelf } from "@/types/shelf";
import { processShelves } from "@/utils/shelves";

export interface ShelvesGridProps {
  /** Callback to expose selection state to parent. */
  onSelectionChange?: (selectedIds: Set<number>) => void;
  /** Callback when shelf is clicked (to navigate to library tab and filter). */
  onShelfClick?: (shelfId: number) => void;
  /** Ref to expose selection control methods to parent. */
  selectionControlRef?: React.MutableRefObject<{
    clearSelection: () => void;
  } | null>;
}

/**
 * Shelves grid component for displaying shelves in grid view.
 *
 * Uses ShelvesContext for global state management, ensuring changes
 * propagate to all components (e.g., Sidebar). Follows SOC by separating
 * data fetching (context) from presentation (component). Follows SRP by
 * delegating shelf display to ShelfCard component. Follows DRY by reusing
 * BooksGrid layout pattern.
 */
export function ShelvesGrid({
  onSelectionChange,
  onShelfClick,
  selectionControlRef,
}: ShelvesGridProps = {}) {
  // Use global context for shelves data (syncs with Sidebar automatically)
  const { shelves, isLoading, error } = useShelvesContext();
  const { canPerformAction } = useUser();

  const [showCreateModal, setShowCreateModal] = useState(false);

  // Manage shelf data updates including cover
  const shelfDataUpdateRef = useRef<{
    updateShelf: (shelfId: number, shelfData: Partial<Shelf>) => void;
    updateCover: (shelfId: number) => void;
  }>({
    updateShelf: () => {},
    updateCover: () => {},
  });
  const { shelfDataOverrides } = useShelfDataUpdates({
    updateRef: shelfDataUpdateRef,
  });

  // Manage shelf selection
  const {
    selectedShelfIds,
    isShelfSelected,
    handleShelfSelect,
    removeFromSelection,
    clearSelection,
  } = useShelfSelection({
    onSelectionChange,
  });

  // Expose clearSelection via ref so external callers can clear selection
  useEffect(() => {
    if (!selectionControlRef) {
      return;
    }
    selectionControlRef.current = {
      clearSelection,
    };
  }, [selectionControlRef, clearSelection]);

  // Handle shelf operations (CRUD)
  const {
    handleShelfUpdate,
    handleCoverUpdate,
    handleShelfDelete,
    handleCreateShelf,
  } = useShelfGridOperations({
    shelfDataUpdateRef,
    onShelvesDeleted: removeFromSelection,
  });

  // Process shelves: deduplicate, apply overrides, and sort
  const uniqueShelves = useMemo(
    () => processShelves(shelves, shelfDataOverrides),
    [shelves, shelfDataOverrides],
  );

  // Check permissions
  const canRead = canPerformAction("shelves", "read");
  const canCreate = canPerformAction("shelves", "create");

  if (error) {
    return (
      <div className="flex min-h-[400px] items-center justify-center p-8">
        <p className="m-0 text-base text-danger-a10">
          Error loading shelves: {error}
        </p>
      </div>
    );
  }

  if (isLoading && uniqueShelves.length === 0) {
    return (
      <div className="flex min-h-[400px] items-center justify-center p-8">
        <p className="m-0 text-base text-text-a40">Loading shelves...</p>
      </div>
    );
  }

  if (!canRead) {
    return (
      <div className="flex min-h-[400px] items-center justify-center p-8">
        <p className="m-0 text-base text-danger-a10">
          You don't have permission to view shelves.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="w-full py-6">
        {uniqueShelves.length > 0 && (
          <div className="px-8 pb-4 text-left text-sm text-text-a40">
            {uniqueShelves.length}{" "}
            {uniqueShelves.length === 1 ? "shelf" : "shelves"}
          </div>
        )}
        <div className="grid grid-cols-[repeat(auto-fit,minmax(140px,200px))] justify-items-start gap-6 px-8 md:grid-cols-[repeat(auto-fit,minmax(160px,200px))] md:gap-[clamp(24px,4vw,50px)] lg:grid-cols-[repeat(auto-fit,minmax(180px,200px))]">
          {uniqueShelves.map((shelf) => (
            <ShelfCard
              key={shelf.id}
              shelf={shelf}
              allShelves={uniqueShelves}
              selected={isShelfSelected(shelf.id)}
              onShelfSelect={handleShelfSelect}
              onShelfUpdate={handleShelfUpdate}
              onCoverUpdate={handleCoverUpdate}
              onShelfDelete={handleShelfDelete}
              selectedShelfIds={selectedShelfIds}
              onShelfClick={onShelfClick}
            />
          ))}
          {/* Show "Create shelf" card only if user has create permission */}
          {canCreate && (
            <CreateShelfCard onClick={() => setShowCreateModal(true)} />
          )}
        </div>
      </div>
      {showCreateModal && (
        <ShelfEditModal
          shelf={null}
          onClose={() => setShowCreateModal(false)}
          onSave={async (data) => {
            const newShelf = await handleCreateShelf(data);
            setShowCreateModal(false);
            return newShelf;
          }}
        />
      )}
    </>
  );
}
