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

/**
 * Props for IconButton component.
 */
export interface IconButtonProps {
  /** PrimeIcons icon class name (e.g., "pi-info-circle"). */
  icon: string;
  /** Accessibility label and tooltip text. */
  label: string;
  /** Whether button is disabled. */
  disabled?: boolean;
  /** Click handler. */
  onClick?: () => void;
}

/**
 * Icon button component for format actions.
 *
 * Reusable button with consistent styling for format action buttons.
 * Follows DRY by eliminating duplicated button styling.
 * Follows SRP by focusing solely on button presentation.
 *
 * Parameters
 * ----------
 * props : IconButtonProps
 *     Component props including icon, label, and handlers.
 */
export function IconButton({
  icon,
  label,
  disabled,
  onClick,
}: IconButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="flex flex-shrink-0 items-center justify-center rounded bg-transparent p-1.5 text-text-a30 transition-[transform,color,background-color] duration-200 hover:bg-surface-a20 hover:text-primary-a0 focus:outline focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
      aria-label={label}
      title={label}
    >
      <span className={`pi ${icon}`} aria-hidden="true" />
    </button>
  );
}
