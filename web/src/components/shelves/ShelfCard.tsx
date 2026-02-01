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
import { FaWandMagicSparkles } from "react-icons/fa6";
import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { BookCardOverlay } from "@/components/library/BookCardOverlay";
import { ReadListBadge } from "@/components/shelves/ReadListBadge";
import { ShelfCardCheckbox } from "@/components/shelves/ShelfCardCheckbox";
import { ShelfCardCover } from "@/components/shelves/ShelfCardCover";
import { ShelfCardEditButton } from "@/components/shelves/ShelfCardEditButton";
import { ShelfCardMenu } from "@/components/shelves/ShelfCardMenu";
import { ShelfCardMenuButton } from "@/components/shelves/ShelfCardMenuButton";
import { ShelfCardMetadata } from "@/components/shelves/ShelfCardMetadata";
import { ShelfEditModal } from "@/components/shelves/ShelfEditModal";
import { useUser } from "@/contexts/UserContext";
import { useBookCardMenu } from "@/hooks/useBookCardMenu";
import { useShelfCardAnimation } from "@/hooks/useShelfCardAnimation";
import { useShelfCardClick } from "@/hooks/useShelfCardClick";
import { useShelfCardMenuActions } from "@/hooks/useShelfCardMenuActions";
import { useShelfEditModal } from "@/hooks/useShelfEditModal";
import { cn } from "@/libs/utils";
import type { Shelf } from "@/types/shelf";
import { buildShelfPermissionContext } from "@/utils/permissions";

type ShelfBooksPreviewResponse = {
  book_ids?: number[];
};

export interface ShelfCardProps {
  /** Shelf data to display. */
  shelf: Shelf;
  /** All shelves in the grid (needed for range selection). */
  allShelves: Shelf[];
  /** Whether the shelf is selected. */
  selected: boolean;
  /** Handler for shelf selection. */
  onShelfSelect: (
    shelf: Shelf,
    allShelves: Shelf[],
    event: React.MouseEvent,
  ) => void;
  /** Callback fired when edit button is clicked. */
  onEdit?: (shelfId: number) => void;
  /** Handler for shelf update. */
  onShelfUpdate?: (shelf: Shelf) => Promise<void>;
  /** Handler for cover update (to refresh cover after upload/delete). */
  onCoverUpdate?: (shelfId: number, updatedShelf?: Shelf) => void;
  /** Handler for shelf deletion. */
  onShelfDelete?: (shelfIds: number | number[]) => Promise<void>;
  /** Set of selected shelf IDs (for bulk operations). */
  selectedShelfIds?: Set<number>;
  /** Callback when shelf card is clicked (to navigate to library tab and filter). */
  onShelfClick?: (shelfId: number) => void;
}

/**
 * Shelf card component for displaying a single shelf in the grid.
 *
 * Orchestrates shelf card display by composing specialized components.
 * Follows SRP by delegating to specialized components and hooks.
 * Uses IOC via hooks and component composition.
 * Follows SOC by separating concerns into independent components.
 * Follows DRY by reusing extracted components and utilities.
 */
export function ShelfCard({
  shelf,
  allShelves,
  selected,
  onShelfSelect,
  onEdit,
  onShelfUpdate,
  onCoverUpdate,
  onShelfDelete,
  selectedShelfIds,
  onShelfClick,
}: ShelfCardProps) {
  const menu = useBookCardMenu();
  const cardRef = useRef<HTMLButtonElement>(null);
  // API/frontend convention is lowercase, but tolerate uppercase just in case.
  const shelfType = shelf.shelf_type as unknown as string;
  const isMagicShelf =
    shelfType === "magic_shelf" || shelfType === "MAGIC_SHELF";
  const hasCustomCover = Boolean(shelf.cover_picture);

  const [magicShelfCoverBookIds, setMagicShelfCoverBookIds] = useState<
    number[]
  >([]);

  const shouldUseMagicShelfGridCover = isMagicShelf && !hasCustomCover;

  useEffect(() => {
    if (!shouldUseMagicShelfGridCover) {
      setMagicShelfCoverBookIds([]);
      return;
    }

    const abortController = new AbortController();

    async function loadMagicShelfCoverBooks() {
      try {
        const maxCandidates = 50;
        const tryFetch = async (sortBy: string) => {
          const queryParams = new URLSearchParams({
            page: "1",
            page_size: maxCandidates.toString(),
            sort_by: sortBy,
            sort_order: "asc",
          });

          return fetch(
            `/api/shelves/${shelf.id}/books?${queryParams.toString()}`,
            {
              signal: abortController.signal,
              cache: "no-store",
            },
          );
        };

        // Prefer backend-driven randomization for Magic Shelf covers.
        // Fallback to deterministic "order" if the backend doesn't support it.
        const response = await (async () => {
          const randomResponse = await tryFetch("random");
          if (randomResponse.ok) {
            return randomResponse;
          }
          return tryFetch("order");
        })();

        if (!response.ok) {
          setMagicShelfCoverBookIds([]);
          return;
        }

        const data = (await response.json()) as ShelfBooksPreviewResponse;
        const bookIds = Array.isArray(data.book_ids) ? data.book_ids : [];

        setMagicShelfCoverBookIds(bookIds.slice(0, 4));
      } catch (err) {
        if ((err as { name?: string } | null)?.name === "AbortError") {
          return;
        }
        setMagicShelfCoverBookIds([]);
      }
    }

    void loadMagicShelfCoverBooks();

    return () => {
      abortController.abort();
    };
  }, [shouldUseMagicShelfGridCover, shelf.id]);

  const magicShelfCoverUrls = useMemo(() => {
    return magicShelfCoverBookIds
      .slice(0, 4)
      .map((bookId) => `/api/books/${bookId}/cover`);
  }, [magicShelfCoverBookIds]);

  const magicShelfGridLayout = useMemo(() => {
    const count = magicShelfCoverUrls.length;
    if (count <= 1) return "one";
    if (count === 2) return "two";
    if (count === 3) return "three";
    return "four";
  }, [magicShelfCoverUrls.length]);

  const { isShaking, isGlowing, triggerAnimation } = useShelfCardAnimation();

  const { handleClick, handleKeyDown } = useShelfCardClick({
    shelf,
    onShelfClick,
    onTriggerAnimation: triggerAnimation,
  });

  const {
    showEditModal,
    closeEditModal,
    handleEditClick,
    handleShelfSave,
    handleCoverSaved,
    handleCoverDeleted,
  } = useShelfEditModal({
    shelf,
    onEdit,
    onShelfUpdate,
    onCoverUpdate,
  });

  const menuActions = useShelfCardMenuActions({
    shelf,
    onShelfDeleted: async () => {
      if (onShelfDelete) {
        // If multiple shelves are selected, delete all selected shelves
        // Otherwise, delete just this shelf
        const idsToDelete =
          selectedShelfIds && selectedShelfIds.size > 1
            ? Array.from(selectedShelfIds)
            : shelf.id;
        await onShelfDelete(idsToDelete);
      }
    },
  });

  const { canPerformAction } = useUser();
  const shelfContext = buildShelfPermissionContext(shelf);
  const canEdit = canPerformAction("shelves", "edit", shelfContext);
  const canDelete = canPerformAction("shelves", "delete", shelfContext);

  return (
    <>
      <button
        ref={cardRef}
        type="button"
        className={cn(
          "group flex cursor-pointer flex-col overflow-hidden rounded",
          "w-full max-w-[200px] border-2 bg-gradient-to-b from-surface-a0 to-surface-a10 p-0 text-left",
          "transition-[transform,box-shadow,border-color] duration-500 ease-out",
          "hover:-translate-y-0.5 hover:shadow-card-hover",
          "focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2",
          "focus:not-focus-visible:outline-none focus:outline-none",
          selected && "border-primary-a0 shadow-primary-glow outline-none",
          !selected && !isGlowing && "border-transparent",
          isShaking && "animate-[shake_0.5s_ease-in-out]",
          isGlowing && "border-warning-a10",
          isGlowing && "shadow-[var(--shadow-warning-glow)]",
        )}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        aria-label={`Shelf: ${shelf.name}`}
        data-shelf-card
      >
        <div className="relative">
          {hasCustomCover ? (
            <ShelfCardCover
              shelfName={shelf.name}
              shelfId={shelf.id}
              hasCoverPicture
            />
          ) : shouldUseMagicShelfGridCover && magicShelfCoverUrls.length > 0 ? (
            <div className="relative aspect-[2/3] w-full overflow-hidden">
              <div
                className={cn(
                  "h-full w-full overflow-hidden bg-gradient-to-br from-surface-a20 to-surface-a10",
                  magicShelfGridLayout === "one" &&
                    "grid grid-cols-1 grid-rows-1",
                  magicShelfGridLayout === "two" &&
                    "grid grid-cols-1 grid-rows-2",
                  magicShelfGridLayout === "three" &&
                    "grid grid-cols-2 grid-rows-2",
                  magicShelfGridLayout === "four" &&
                    "grid grid-cols-2 grid-rows-2",
                )}
              >
                {magicShelfCoverUrls.map((url, idx) => {
                  const isThirdInThree =
                    magicShelfGridLayout === "three" && idx === 2;
                  return (
                    <div
                      key={url}
                      className={cn(
                        "relative h-full w-full overflow-hidden",
                        isThirdInThree && "col-span-2",
                      )}
                    >
                      <ImageWithLoading
                        src={url}
                        alt={`Cover preview ${idx + 1} for ${shelf.name}`}
                        width={200}
                        height={300}
                        className="h-full w-full object-cover"
                        containerClassName="w-full h-full"
                        unoptimized
                      />
                      <div className="absolute inset-0 ring-1 ring-surface-a0/20" />
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <ShelfCardCover
              shelfName={shelf.name}
              shelfId={shelf.id}
              hasCoverPicture={false}
            />
          )}
          {isMagicShelf && (
            <div
              className={cn(
                "pointer-events-none absolute top-2 right-2 z-20",
                "flex h-7 w-7 items-center justify-center rounded-full",
                "bg-surface-a0/50 text-warning-a10 backdrop-blur-sm",
              )}
              title="Magic shelf"
              aria-hidden="true"
              data-magic-shelf-icon
            >
              <FaWandMagicSparkles className="h-4 w-4" />
            </div>
          )}
          <BookCardOverlay selected={selected}>
            <ShelfCardCheckbox
              shelf={shelf}
              allShelves={allShelves}
              selected={selected}
              onShelfSelect={onShelfSelect}
            />
            {canEdit && (
              <ShelfCardEditButton
                shelfName={shelf.name}
                onEdit={handleEditClick}
              />
            )}
            {canDelete && (
              <ShelfCardMenuButton
                buttonRef={menu.menuButtonRef}
                isMenuOpen={menu.isMenuOpen}
                onToggle={menu.handleMenuToggle}
              />
            )}
          </BookCardOverlay>
        </div>
        <ShelfCardMetadata
          name={shelf.name}
          bookCount={shelf.book_count}
          isPublic={shelf.is_public}
        />
        <div className="px-3 pb-3">
          <ReadListBadge shelfType={shelf.shelf_type} />
        </div>
      </button>
      {canDelete && (
        <ShelfCardMenu
          isOpen={menu.isMenuOpen}
          onClose={menu.handleMenuClose}
          buttonRef={menu.menuButtonRef}
          cursorPosition={menu.cursorPosition}
          onDelete={menuActions.handleDelete}
          shelf={shelf}
        />
      )}
      {showEditModal && (
        <ShelfEditModal
          shelf={shelf}
          onClose={closeEditModal}
          onSave={handleShelfSave}
          onCoverSaved={handleCoverSaved}
          onCoverDeleted={handleCoverDeleted}
        />
      )}
    </>
  );
}
