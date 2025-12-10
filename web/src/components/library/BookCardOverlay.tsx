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

export interface BookCardOverlayProps {
  /** Whether the book is selected. */
  selected: boolean;
  /** Overlay content (buttons). */
  children: React.ReactNode;
}

/**
 * Book card overlay component.
 *
 * Provides overlay background and visibility states for overlay buttons.
 * Follows SRP by focusing solely on overlay styling and state management.
 * Uses IOC via children prop for button composition.
 */
export function BookCardOverlay({ selected, children }: BookCardOverlayProps) {
  return (
    <div
      className={cn(
        "absolute inset-0 z-10 transition-[opacity,background-color] duration-200 ease-in-out",
        // Default state: hidden
        "pointer-events-none bg-black/50 opacity-0",
        // When selected: visible but transparent, hide edit/menu buttons
        selected && "bg-transparent opacity-100",
        selected &&
          "[&_.edit-button]:pointer-events-none [&_.edit-button]:opacity-0",
        selected &&
          "[&_.menu-button]:pointer-events-none [&_.menu-button]:opacity-0",
        // On hover: show overlay and all buttons (using parent button's group)
        "group-hover:bg-black/50 group-hover:opacity-100",
        // Capture pointer events on overlay to allow cursor-default override,
        // preventing the pointer cursor from the parent button.
        "cursor-default group-hover:pointer-events-auto",
        "group-hover:[&_.edit-button]:pointer-events-auto group-hover:[&_.edit-button]:opacity-100",
        "group-hover:[&_.menu-button]:pointer-events-auto group-hover:[&_.menu-button]:opacity-100",
        "group-hover:[&_.checkbox]:pointer-events-auto",
        "flex items-center justify-center",
      )}
    >
      {children}
    </div>
  );
}
