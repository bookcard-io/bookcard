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

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ShelfCard } from "@/components/shelves/ShelfCard";
import { ShelfEditModal } from "@/components/shelves/ShelfEditModal";
import { useShelvesContext } from "@/contexts/ShelvesContext";
import { useShelfDataUpdates } from "@/hooks/useShelfDataUpdates";
import { useShelves } from "@/hooks/useShelves";
import { cn } from "@/libs/utils";
import { deleteShelf } from "@/services/shelfService";
import type { Shelf, ShelfCreate, ShelfUpdate } from "@/types/shelf";
import { createEnterSpaceHandler } from "@/utils/keyboard";
import { deduplicateShelves } from "@/utils/shelves";

export interface ShelvesGridProps {
  /** Callback to expose selection state to parent. */
  onSelectionChange?: (selectedIds: Set<number>) => void;
  /** Callback when shelf is clicked (to navigate to library tab and filter). */
  onShelfClick?: (shelfId: number) => void;
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
}: ShelvesGridProps = {}) {
  // Use global context for shelves data (syncs with Sidebar automatically)
  const {
    shelves,
    isLoading,
    error,
    refresh: refreshContext,
  } = useShelvesContext();
  // Use hook for mutations
  const { updateShelf, createShelf } = useShelves();
  const [selectedShelfIds, setSelectedShelfIds] = useState<Set<number>>(
    new Set(),
  );
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Store callback in ref to avoid dependency issues and prevent calling during render
  const onSelectionChangeRef = useRef(onSelectionChange);
  useEffect(() => {
    onSelectionChangeRef.current = onSelectionChange;
  }, [onSelectionChange]);

  // Notify parent of selection changes (deferred to avoid setState during render)
  useEffect(() => {
    onSelectionChangeRef.current?.(selectedShelfIds);
  }, [selectedShelfIds]);

  // Manage shelf data updates including cover (SRP: shelf data state management separated)
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

  // Handle shelf selection
  const handleShelfSelect = useCallback(
    (shelf: Shelf, _allShelves: Shelf[], event: React.MouseEvent) => {
      if (event?.stopPropagation) {
        event.stopPropagation();
      }
      setSelectedShelfIds((prev) => {
        const newSet = new Set(prev);
        if (newSet.has(shelf.id)) {
          newSet.delete(shelf.id);
        } else {
          newSet.add(shelf.id);
        }
        // Don't call onSelectionChange here - let useEffect handle it
        return newSet;
      });
    },
    [],
  );

  // Handle shelf update
  const handleShelfUpdate = useCallback(
    async (shelf: Shelf) => {
      await updateShelf(shelf.id, {
        name: shelf.name,
        description: shelf.description,
        is_public: shelf.is_public,
      });
      // Refresh context to sync with Sidebar and other components
      await refreshContext();
      // Update local state to reflect changes without full refresh
      shelfDataUpdateRef.current?.updateShelf(shelf.id, {
        name: shelf.name,
        description: shelf.description,
        is_public: shelf.is_public,
      });
    },
    [updateShelf, refreshContext],
  );

  // Handle cover update (for refreshing cover after upload/delete)
  const handleCoverUpdate = useCallback(
    (shelfId: number, updatedShelf?: Shelf) => {
      if (updatedShelf) {
        // Update shelf data with the actual updated shelf from API
        shelfDataUpdateRef.current?.updateShelf(shelfId, {
          cover_picture: updatedShelf.cover_picture,
        });
      } else {
        // Fallback: just trigger cover refresh with cache-busting
        shelfDataUpdateRef.current?.updateCover(shelfId);
      }
    },
    [],
  );

  // Check if shelf is selected
  const isShelfSelected = useCallback(
    (shelfId: number) => selectedShelfIds.has(shelfId),
    [selectedShelfIds],
  );

  // Handle shelf deletion (single or multiple)
  const handleShelfDelete = useCallback(
    async (shelfIds: number | number[]) => {
      const idsToDelete = Array.isArray(shelfIds) ? shelfIds : [shelfIds];

      try {
        // Delete all shelves in parallel
        await Promise.all(idsToDelete.map((id) => deleteShelf(id)));

        // Remove deleted shelves from selection
        setSelectedShelfIds((prev) => {
          const newSet = new Set(prev);
          for (const id of idsToDelete) {
            newSet.delete(id);
          }
          // Don't call onSelectionChange here - let useEffect handle it
          return newSet;
        });

        // Refresh context to sync with Sidebar and other components
        await refreshContext();
      } catch (error) {
        console.error("Failed to delete shelf(s):", error);
        // Error handling could be improved with user notification
      }
    },
    [refreshContext],
  );

  // Handle shelf creation
  const handleCreateShelf = useCallback(
    async (data: ShelfCreate | ShelfUpdate): Promise<Shelf> => {
      const newShelf = await createShelf(data as ShelfCreate);
      setShowCreateModal(false);
      // Refresh context to sync with Sidebar and other components
      await refreshContext();
      return newShelf;
    },
    [createShelf, refreshContext],
  );

  // Deduplicate shelves and apply shelf data overrides, then sort by created_at desc
  const uniqueShelves = useMemo(() => {
    const deduplicated = deduplicateShelves(shelves, shelfDataOverrides);
    // Sort by created_at descending (newest first)
    return [...deduplicated].sort((a, b) => {
      const dateA = new Date(a.created_at).getTime();
      const dateB = new Date(b.created_at).getTime();
      return dateB - dateA; // Descending order
    });
  }, [shelves, shelfDataOverrides]);

  // Handle add shelf card click
  const handleAddShelfClick = useCallback(() => {
    setShowCreateModal(true);
  }, []);

  const handleAddShelfKeyDown = createEnterSpaceHandler(handleAddShelfClick);

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
          {/* Always show "Create shelf" card as the last item */}
          <button
            type="button"
            className={cn(
              "group flex cursor-pointer flex-col overflow-hidden rounded",
              "w-full max-w-[200px] border-2 border-surface-a30 border-dashed bg-gradient-to-b from-surface-a0 to-surface-a10 p-0 text-left",
              "transition-[transform,box-shadow,border-color] duration-200 ease-out",
              "hover:-translate-y-0.5 hover:border-primary-a0 hover:shadow-card-hover",
              "focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2",
              "focus:not-focus-visible:outline-none focus:outline-none",
            )}
            onClick={handleAddShelfClick}
            onKeyDown={handleAddShelfKeyDown}
            aria-label="Create new shelf"
          >
            <div className="relative aspect-[2/3] w-full overflow-hidden">
              <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-surface-a20 to-surface-a10">
                <i
                  className="pi pi-plus text-4xl text-text-a30 transition-colors duration-200 group-hover:text-primary-a0"
                  aria-hidden="true"
                />
              </div>
            </div>
            <div className="flex min-h-16 flex-col gap-1 bg-surface-a10 p-[0.75rem]">
              <h3 className="m-0 line-clamp-2 font-[500] text-[0.875rem] text-text-a30 leading-[1.3]">
                Create shelf
              </h3>
            </div>
          </button>
        </div>
      </div>
      {showCreateModal && (
        <ShelfEditModal
          shelf={null}
          onClose={() => setShowCreateModal(false)}
          onSave={handleCreateShelf}
        />
      )}
    </>
  );
}
