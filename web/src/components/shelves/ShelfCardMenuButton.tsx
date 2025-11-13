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

import { BookCardMenuButton } from "@/components/library/BookCardMenuButton";

export interface ShelfCardMenuButtonProps {
  /** Reference to the button element. */
  buttonRef: React.RefObject<HTMLDivElement | null>;
  /** Whether the menu is open. */
  isMenuOpen: boolean;
  /** Handler for menu toggle. */
  onToggle: (e: React.MouseEvent<HTMLDivElement>) => void;
}

/**
 * Menu button overlay for shelf card.
 *
 * Handles menu button interaction.
 * Follows SRP by focusing solely on menu button UI and behavior.
 * Uses IOC via callback prop.
 * Follows DRY by reusing BookCardMenuButton component.
 */
export function ShelfCardMenuButton({
  buttonRef,
  isMenuOpen,
  onToggle,
}: ShelfCardMenuButtonProps) {
  return (
    <BookCardMenuButton
      buttonRef={buttonRef}
      isMenuOpen={isMenuOpen}
      onToggle={onToggle}
      variant="grid"
    />
  );
}
