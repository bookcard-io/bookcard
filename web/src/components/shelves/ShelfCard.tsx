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

import { useCallback, useRef, useState } from "react";
import { BookCardOverlay } from "@/components/library/BookCardOverlay";
import { ShelfCardCheckbox } from "@/components/shelves/ShelfCardCheckbox";
import { ShelfCardCover } from "@/components/shelves/ShelfCardCover";
import { ShelfCardEditButton } from "@/components/shelves/ShelfCardEditButton";
import { ShelfCardMenu } from "@/components/shelves/ShelfCardMenu";
import { ShelfCardMenuButton } from "@/components/shelves/ShelfCardMenuButton";
import { ShelfCardMetadata } from "@/components/shelves/ShelfCardMetadata";
import { ShelfEditModal } from "@/components/shelves/ShelfEditModal";
import { useBookCardMenu } from "@/hooks/useBookCardMenu";
import { useShelfCardMenuActions } from "@/hooks/useShelfCardMenuActions";
import { cn } from "@/libs/utils";
import type { Shelf, ShelfCreate, ShelfUpdate } from "@/types/shelf";
import { createEnterSpaceHandler } from "@/utils/keyboard";

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
  const [showEditModal, setShowEditModal] = useState(false);
  const [isShaking, setIsShaking] = useState(false);
  const [isGlowing, setIsGlowing] = useState(false);
  const cardRef = useRef<HTMLButtonElement>(null);

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

  /**
   * Handle shelf card click.
   */
  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      // Don't trigger if clicking on overlay buttons (checkbox, edit, menu)
      const target = e.target as HTMLElement;
      if (
        target.closest("[data-shelf-checkbox]") ||
        target.closest("[data-shelf-edit]") ||
        target.closest("[data-shelf-menu]")
      ) {
        return;
      }

      if (shelf.book_count === 0) {
        // Empty shelf: trigger shake and red glow animation
        setIsShaking(true);
        setIsGlowing(true);
        // Reset shake after animation completes
        setTimeout(() => {
          setIsShaking(false);
        }, 500);
        // Fade out red glow after shake completes
        setTimeout(() => {
          setIsGlowing(false);
        }, 1000);
      } else {
        // Shelf has books: navigate to library tab and filter
        onShelfClick?.(shelf.id);
      }
    },
    [shelf.book_count, shelf.id, onShelfClick],
  );

  const handleKeyDown = createEnterSpaceHandler(() => {
    // For keyboard interactions, we don't need to check for overlay buttons
    // since keyboard focus won't be on those elements
    if (shelf.book_count === 0) {
      // Empty shelf: trigger shake and red glow animation
      setIsShaking(true);
      setIsGlowing(true);
      // Reset shake after animation completes
      setTimeout(() => {
        setIsShaking(false);
      }, 500);
      // Fade out red glow after shake completes
      setTimeout(() => {
        setIsGlowing(false);
      }, 1000);
    } else {
      // Shelf has books: navigate to library tab and filter
      onShelfClick?.(shelf.id);
    }
  });

  const handleEditClick = useCallback(() => {
    if (onEdit) {
      onEdit(shelf.id);
    } else {
      setShowEditModal(true);
    }
  }, [onEdit, shelf.id]);

  const handleShelfSave = useCallback(
    async (data: ShelfCreate | ShelfUpdate): Promise<Shelf> => {
      if (onShelfUpdate) {
        const updatedShelf = { ...shelf, ...data } as Shelf;
        await onShelfUpdate(updatedShelf);
        setShowEditModal(false);
        return updatedShelf;
      }
      setShowEditModal(false);
      return shelf;
    },
    [onShelfUpdate, shelf],
  );

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
          <ShelfCardCover
            shelfName={shelf.name}
            shelfId={shelf.id}
            hasCoverPicture={Boolean(shelf.cover_picture)}
          />
          <BookCardOverlay selected={selected}>
            <ShelfCardCheckbox
              shelf={shelf}
              allShelves={allShelves}
              selected={selected}
              onShelfSelect={onShelfSelect}
            />
            <ShelfCardEditButton
              shelfName={shelf.name}
              onEdit={handleEditClick}
            />
            <ShelfCardMenuButton
              buttonRef={menu.menuButtonRef}
              isMenuOpen={menu.isMenuOpen}
              onToggle={menu.handleMenuToggle}
            />
          </BookCardOverlay>
        </div>
        <ShelfCardMetadata
          name={shelf.name}
          bookCount={shelf.book_count}
          isPublic={shelf.is_public}
        />
      </button>
      <ShelfCardMenu
        isOpen={menu.isMenuOpen}
        onClose={menu.handleMenuClose}
        buttonRef={menu.menuButtonRef}
        cursorPosition={menu.cursorPosition}
        onDelete={menuActions.handleDelete}
      />
      {showEditModal && (
        <ShelfEditModal
          shelf={shelf}
          onClose={() => setShowEditModal(false)}
          onSave={handleShelfSave}
          onCoverSaved={(updatedShelf) => {
            // Update cover in grid when cover is saved (O(1) operation)
            onCoverUpdate?.(updatedShelf.id, updatedShelf);
          }}
          onCoverDeleted={(updatedShelf) => {
            // Update cover in grid when cover is deleted (O(1) operation)
            onCoverUpdate?.(updatedShelf.id, updatedShelf);
          }}
        />
      )}
    </>
  );
}
