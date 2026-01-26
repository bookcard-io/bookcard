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

import { useCallback, useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { useFlyoutIntent } from "@/hooks/useFlyoutIntent";
import { useFlyoutPosition } from "@/hooks/useFlyoutPosition";
import { useMoreFromSameFilters } from "@/hooks/useMoreFromSameFilters";
import { cn } from "@/libs/utils";
import type { Book } from "@/types/book";
import { getFlyoutPositionStyle } from "@/utils/flyoutPositionStyle";

export interface MoreFromSameFlyoutMenuProps {
  /** Whether the flyout menu is open. */
  isOpen: boolean;
  /** Reference to the parent menu item element. */
  parentItemRef: React.RefObject<HTMLElement | null>;
  /** Book to derive filters from. */
  book: Book;
  /** Callback when menu should be closed. */
  onClose: () => void;
  /** Callback when mouse enters the flyout (to keep parent menu item hovered). */
  onMouseEnter?: () => void;
  /** Callback on successful action (to close parent menu). */
  onSuccess?: () => void;
  /** Callback to close parent menu (for Esc key handling). */
  onCloseParent?: () => void;
}

/**
 * Flyout menu for applying "More from the same..." filters.
 *
 * Presents quick filter options derived from the selected book:
 * - Author (first author only)
 * - Series
 * - Genre (first tag only)
 * - Publisher
 *
 * Filters are applied through LibraryFiltersContext so they sync with FiltersPanel.
 * For the selected filter type, values are replaced (not merged), while other filter
 * types are preserved.
 *
 * Parameters
 * ----------
 * props : MoreFromSameFlyoutMenuProps
 *     Component props including open state, parent ref, book, and callbacks.
 */
export function MoreFromSameFlyoutMenu({
  isOpen,
  parentItemRef,
  book,
  onClose,
  onMouseEnter,
  onSuccess,
  onCloseParent,
}: MoreFromSameFlyoutMenuProps) {
  const [mounted, setMounted] = useState(false);
  const { showDanger } = useGlobalMessages();

  const {
    canApplyAuthor,
    canApplySeries,
    canApplyGenre,
    canApplyPublisher,
    isGenreLookupLoading,
    genreLookupError,
    apply,
  } = useMoreFromSameFilters({ book, enabled: isOpen });

  const { position, direction, menuRef } = useFlyoutPosition({
    isOpen,
    parentItemRef,
    mounted,
  });

  useEffect(() => {
    setMounted(true);
  }, []);

  useFlyoutIntent({
    isOpen,
    parentItemRef,
    menuRef,
    onClose,
    padding: 10,
    minMovementPx: 2,
    idleTimeMs: 20,
  });

  const handleFlyoutMouseEnter = useCallback(() => {
    onMouseEnter?.();
  }, [onMouseEnter]);

  const applyAndClose = useCallback(
    async (filterType: "author" | "series" | "genre" | "publisher") => {
      try {
        await apply(filterType);
        onClose();
        onSuccess?.();
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Failed to apply filter";
        showDanger(message);
      }
    },
    [apply, onClose, onSuccess, showDanger],
  );

  // Handle Esc key to close menus
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        onClose();
        onCloseParent?.();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose, onCloseParent]);

  if (!isOpen || !mounted) {
    return null;
  }

  const genreDisabled =
    !canApplyGenre || isGenreLookupLoading || !!genreLookupError;

  const menuContent = (
    <div
      ref={menuRef}
      className={cn(
        "fixed z-[10000] rounded-md",
        "border border-surface-tonal-a20 bg-surface-tonal-a10",
        "shadow-black/50 shadow-lg",
        "overflow-hidden",
        "min-w-[220px]",
      )}
      style={getFlyoutPositionStyle(position, direction)}
      role="menu"
      aria-label="More from the same"
      onMouseDown={(e) => e.stopPropagation()}
      onMouseEnter={handleFlyoutMouseEnter}
      data-keep-selection
    >
      <div className="py-1">
        <DropdownMenuItem
          label="Author"
          onClick={
            canApplyAuthor ? () => void applyAndClose("author") : undefined
          }
          disabled={!canApplyAuthor}
        />
        <DropdownMenuItem
          label="Series"
          onClick={
            canApplySeries ? () => void applyAndClose("series") : undefined
          }
          disabled={!canApplySeries}
        />
        <DropdownMenuItem
          label={isGenreLookupLoading ? "Genre (loading...)" : "Genre"}
          onClick={
            genreDisabled ? undefined : () => void applyAndClose("genre")
          }
          disabled={genreDisabled}
        />
        <DropdownMenuItem
          label="Publisher"
          onClick={
            canApplyPublisher
              ? () => void applyAndClose("publisher")
              : undefined
          }
          disabled={!canApplyPublisher}
        />
      </div>
    </div>
  );

  return createPortal(menuContent, document.body);
}
