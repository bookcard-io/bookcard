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

interface ToggleButtonProps {
  /**
   * Button label text.
   */
  label: string;
  /**
   * Whether the button is currently selected/active.
   */
  isSelected: boolean;
  /**
   * Callback fired when button is clicked.
   */
  onClick: (e: React.MouseEvent<HTMLButtonElement>) => void;
}

/**
 * Toggle button component for multi-select options.
 *
 * Displays a button that can be toggled on/off.
 * Follows SRP by handling only button UI and click events.
 *
 * Parameters
 * ----------
 * label : string
 *     Button label text.
 * isSelected : boolean
 *     Whether the button is currently selected.
 * onClick : (e: React.MouseEvent<HTMLButtonElement>) => void
 *     Callback fired when button is clicked.
 */
export function ToggleButton({
  label,
  isSelected,
  onClick,
}: ToggleButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded border px-3 py-1.5 font-medium text-sm transition-colors duration-200",
        isSelected
          ? "border-primary-a0 bg-primary-a0 text-text-a0"
          : "border-surface-a20 bg-surface-tonal-a10 text-text-a0 hover:bg-surface-tonal-a20",
      )}
      aria-pressed={isSelected}
    >
      {label}
    </button>
  );
}
