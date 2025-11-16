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

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useDragReorder } from "@/hooks/useDragReorder";
import { useDropdownClickOutside } from "@/hooks/useDropdownClickOutside";
import { useListColumns } from "@/hooks/useListColumns";
import { cn } from "@/libs/utils";
import { ColumnItem } from "./ColumnItem";
import { useColumnData } from "./useColumnData";

export interface ListColumnSelectorProps {
  /** Whether the selector is open. */
  isOpen: boolean;
  /** Callback when selector should be closed. */
  onClose: () => void;
  /** Reference to the button element (for click outside detection). */
  buttonRef: React.RefObject<HTMLElement | null>;
}

/**
 * Column selector component for list view.
 *
 * Orchestrates column selection UI by composing specialized hooks and components.
 * Follows SRP by delegating to specialized hooks and components.
 * Follows SOC by separating drag-and-drop, data transformation, and rendering concerns.
 * Follows IOC via hooks and component composition.
 * Follows DRY by reusing extracted components and hooks.
 * Follows SOLID principles via dependency inversion and single responsibility.
 */
export function ListColumnSelector({
  isOpen,
  onClose,
  buttonRef,
}: ListColumnSelectorProps) {
  const { visibleColumns, allColumns, toggleColumn, reorderColumns } =
    useListColumns();
  const menuRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState<{
    top: number;
    right: number;
  } | null>(null);

  // Separate concerns: data transformation
  const { orderedVisibleColumns, nonVisibleColumns } = useColumnData(
    visibleColumns,
    allColumns,
  );

  // Separate concerns: drag-and-drop logic
  const dragReorder = useDragReorder({
    onReorder: reorderColumns,
  });

  // Separate concerns: click outside detection
  useDropdownClickOutside({
    isOpen,
    buttonRef,
    menuRef,
    onClose,
  });

  // Calculate position based on button location (for portal rendering)
  useEffect(() => {
    if (!isOpen || !buttonRef.current) {
      setPosition(null);
      return;
    }

    const updatePosition = () => {
      if (!buttonRef.current) {
        return;
      }

      const rect = buttonRef.current.getBoundingClientRect();

      // Position below the button, aligned to the right
      // Using fixed positioning (relative to viewport), so use getBoundingClientRect directly
      setPosition({
        top: rect.bottom + 8, // 8px = mt-2 equivalent
        right: window.innerWidth - rect.right,
      });
    };

    updatePosition();

    // Update position on scroll and resize
    const handleScroll = () => updatePosition();
    const handleResize = () => updatePosition();

    const scrollContainer = document.querySelector(
      '[data-page-scroll-container="true"]',
    );
    // Listen to scroll events to update position when button moves
    scrollContainer?.addEventListener("scroll", handleScroll, {
      passive: true,
    });
    window.addEventListener("resize", handleResize);

    return () => {
      scrollContainer?.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleResize);
    };
  }, [isOpen, buttonRef]);

  // Memoized handler for column toggle (IOC: dependency injection)
  const handleToggle = useCallback(
    (columnId: string) => {
      toggleColumn(columnId as (typeof visibleColumns)[number]);
    },
    [toggleColumn],
  );

  if (!isOpen || !position) {
    return null;
  }

  const menuContent = (
    <div
      ref={menuRef}
      className={cn("panel-tonal fixed z-50 w-64 rounded-md shadow-lg")}
      style={{
        top: `${position.top}px`,
        right: `${position.right}px`,
      }}
      role="dialog"
      aria-label="Column selector"
      aria-modal="false"
    >
      <div className="p-4">
        <h3 className="m-0 mb-3 font-semibold text-sm text-text-a0">
          Show Columns (drag to reorder)
        </h3>
        <div className="flex flex-col gap-2">
          {/* Visible columns (draggable) */}
          {orderedVisibleColumns.map((column, index) => {
            const isRequired = column.id === "title" || column.id === "authors";
            const isDragging = dragReorder.draggedIndex === index;
            const isDragOver = dragReorder.dragOverIndex === index;
            const showBeforeIndicator =
              dragReorder.dropIndicator?.index === index &&
              dragReorder.dropIndicator.position === "before";
            const showAfterIndicator =
              dragReorder.dropIndicator?.index === index &&
              dragReorder.dropIndicator.position === "after";

            // Create drag handlers for this specific item (IOC: dependency injection)
            const dragHandlers = isRequired
              ? undefined
              : {
                  onDragStart: () => dragReorder.handleDragStart(index),
                  onDragOver: (e: React.DragEvent<HTMLLabelElement>) =>
                    dragReorder.handleDragOver(e, index),
                  onDragLeave: dragReorder.handleDragLeave,
                  onDrop: (e: React.DragEvent<HTMLLabelElement>) =>
                    dragReorder.handleDrop(e, index),
                  onDragEnd: dragReorder.handleDragEnd,
                };

            return (
              <ColumnItem
                key={column.id}
                column={column}
                checked={true}
                isRequired={isRequired}
                onToggle={handleToggle}
                isDragging={isDragging}
                isDragOver={isDragOver}
                showBeforeIndicator={showBeforeIndicator}
                showAfterIndicator={showAfterIndicator}
                dragHandlers={dragHandlers}
              />
            );
          })}

          {/* Non-visible columns (not draggable, just for toggling) */}
          {nonVisibleColumns.length > 0 && (
            <>
              {orderedVisibleColumns.length > 0 && (
                <div className="my-1 border-surface-a20 border-t" />
              )}
              {nonVisibleColumns.map((column) => (
                <ColumnItem
                  key={column.id}
                  column={column}
                  checked={false}
                  isRequired={false}
                  onToggle={handleToggle}
                />
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );

  // Render in portal to ensure it appears above sticky headers
  return typeof document !== "undefined"
    ? createPortal(menuContent, document.body)
    : null;
}
