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

import type { ReactNode } from "react";

export interface TooltipProps {
  /**
   * The content to display in the tooltip.
   */
  text: string;
  /**
   * The element that triggers the tooltip.
   */
  children: ReactNode;
}

/**
 * Tooltip component styled like Plex.
 *
 * Displays a dark tooltip with white text and an upward-pointing arrow.
 * Follows SRP by only handling tooltip rendering.
 *
 * Parameters
 * ----------
 * props : TooltipProps
 *     Component props including text and children.
 *
 * Examples
 * --------
 * ```tsx
 * <Tooltip text="View profile">
 *   <button>Profile</button>
 * </Tooltip>
 * ```
 */
export function Tooltip({ text, children }: TooltipProps) {
  return (
    <div className="group relative inline-block">
      {children}
      <div className="-translate-x-1/2 pointer-events-none invisible absolute top-full left-1/2 z-50 mt-2 whitespace-nowrap rounded-md bg-[var(--color-surface-a10)] px-3 py-1.5 text-[var(--color-text-a0)] text-sm opacity-0 shadow-lg transition-opacity duration-200 group-hover:visible group-hover:opacity-100">
        {text}
        {/* Arrow pointing down */}
        <div className="-translate-x-1/2 absolute bottom-full left-1/2 border-4 border-transparent border-b-[var(--color-surface-a10)]" />
      </div>
    </div>
  );
}
