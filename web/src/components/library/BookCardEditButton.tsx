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

import { cn } from "@/libs/utils";
import { createEnterSpaceHandler } from "@/utils/keyboard";

export interface BookCardEditButtonProps {
  /** Book title for accessibility. */
  bookTitle: string;
  /** Handler for edit action. */
  onEdit: () => void;
  /** Variant style: 'grid' for overlay on cover, 'list' for inline. */
  variant?: "grid" | "list";
}

/**
 * Edit button overlay for book card.
 *
 * Handles edit button interaction.
 * Follows SRP by focusing solely on edit button UI and behavior.
 * Uses IOC via callback prop.
 */
export function BookCardEditButton({
  bookTitle,
  onEdit,
  variant = "grid",
}: BookCardEditButtonProps) {
  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    e.stopPropagation();
    onEdit();
  };

  const handleKeyDown = createEnterSpaceHandler(() => {
    handleClick({} as React.MouseEvent<HTMLDivElement>);
  });

  const isList = variant === "list";

  return (
    /* biome-ignore lint/a11y/useSemanticElements: Cannot use button inside button, using div with role="button" for accessibility */
    <div
      data-book-edit
      data-shelf-edit
      className={cn(
        "edit-button pointer-events-auto flex cursor-default items-center justify-center",
        "transition-[background-color,transform,opacity] duration-200 ease-in-out",
        "focus:shadow-focus-ring focus:outline-none",
        "active:scale-95",
        "[&_i]:block",
        isList
          ? [
              "relative h-8 w-8 rounded border border-surface-a20 bg-surface-a10 text-text-a0",
              "hover:bg-surface-a20 [&_i]:text-sm",
            ]
          : [
              "absolute bottom-3 left-3 h-10 w-10 rounded-full text-[var(--color-white)]",
              "border-none bg-white/20 backdrop-blur-sm",
              "hover:scale-110 hover:bg-white/30 [&_i]:text-lg",
            ],
      )}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      aria-label={`Edit ${bookTitle}`}
      onKeyDown={handleKeyDown}
    >
      <i className="pi pi-pencil" aria-hidden="true" />
    </div>
  );
}
