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

export interface BookCardMenuButtonProps {
  /** Reference to the button element. */
  buttonRef: React.RefObject<HTMLDivElement | null>;
  /** Whether the menu is open. */
  isMenuOpen: boolean;
  /** Handler for menu toggle. */
  onToggle: (e: React.MouseEvent<HTMLDivElement>) => void;
}

/**
 * Menu button overlay for book card.
 *
 * Handles menu button interaction.
 * Follows SRP by focusing solely on menu button UI and behavior.
 * Uses IOC via callback prop.
 */
export function BookCardMenuButton({
  buttonRef,
  isMenuOpen,
  onToggle,
}: BookCardMenuButtonProps) {
  const handleKeyDown = createEnterSpaceHandler(() => {
    onToggle({} as React.MouseEvent<HTMLDivElement>);
  });

  return (
    <div className="absolute right-3 bottom-3 z-20">
      {/* biome-ignore lint/a11y/useSemanticElements: Cannot use button inside button, using div with role="button" for accessibility */}
      <div
        ref={buttonRef}
        className={cn(
          "menu-button pointer-events-auto flex cursor-default items-center justify-center",
          "text-[var(--color-white)] transition-[background-color,transform,opacity] duration-200 ease-in-out",
          "focus:shadow-focus-ring focus:outline-none",
          "h-10 w-10 rounded-full",
          "border-none bg-white/20 backdrop-blur-sm",
          "hover:scale-110 hover:bg-white/30",
          "active:scale-95",
          "[&_i]:block [&_i]:text-lg",
        )}
        onClick={onToggle}
        role="button"
        tabIndex={0}
        aria-label="Menu"
        aria-haspopup="true"
        aria-expanded={isMenuOpen}
        onKeyDown={handleKeyDown}
      >
        <i className="pi pi-ellipsis-v" aria-hidden="true" />
      </div>
    </div>
  );
}
