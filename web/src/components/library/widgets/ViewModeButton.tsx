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

export interface ViewModeButtonProps {
  /**
   * PrimeIcons class name(s) to display in the button.
   */
  iconClass: string;
  /**
   * Whether this view mode is currently active.
   */
  isActive?: boolean;
  /**
   * Callback fired when the button is clicked.
   */
  onClick?: () => void;
  /**
   * Accessible label for the button.
   */
  ariaLabel: string;
  /**
   * Position in a segmented control group.
   */
  position?: "first" | "last";
}

/**
 * Individual view mode toggle button component.
 *
 * Represents a single view mode option (e.g., grid, list, sort).
 * Follows SRP by handling only button UI and click events.
 */
export function ViewModeButton({
  iconClass,
  isActive = false,
  onClick,
  ariaLabel,
  position,
}: ViewModeButtonProps) {
  const handleClick = () => {
    onClick?.();
  };

  return (
    <button
      type="button"
      className={cn(
        // Base styles
        "flex h-9 w-9 cursor-pointer items-center justify-center p-0",
        "transition-[background-color,color,border-color,box-shadow] duration-200",
        // Rounded corners based on position
        position === "first" && "rounded-r-none rounded-l-lg",
        position === "last" && "-ml-px rounded-r-lg rounded-l-none",
        !position && "rounded-md",
        // Border - full border for all buttons, creates visible separator when touching
        "border border-surface-a20",
        // Active state: lighter background with darker icon
        isActive && ["bg-primary-a20", "text-surface-a20"],
        // Inactive state: darker background with lighter icon
        !isActive && ["bg-surface-a20", "text-text-a0"],
        // Hover states
        "hover:bg-surface-tonal-a20 hover:text-primary-a20",
        "hover:border-primary-a20 hover:shadow-[var(--shadow-primary-glow)]",
        "active:bg-surface-tonal-a30",
      )}
      onClick={handleClick}
      aria-label={ariaLabel}
      aria-pressed={isActive}
    >
      <i className={`pi ${iconClass} shrink-0`} aria-hidden="true" />
    </button>
  );
}
