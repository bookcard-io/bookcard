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

import Link from "next/link";
import type { ReactNode } from "react";
import { Tooltip } from "./Tooltip";

export interface HeaderActionButtonProps {
  /**
   * URL to navigate to when the button is clicked.
   */
  href: string;
  /**
   * Tooltip text to display on hover.
   */
  tooltipText: string;
  /**
   * Accessible label for the button.
   */
  ariaLabel: string;
  /**
   * Content to render inside the button.
   */
  children: ReactNode;
}

/**
 * Base component for header action bar buttons.
 *
 * Provides consistent styling and tooltip functionality for all action bar buttons.
 * Follows DRY by centralizing common button structure.
 * Follows SRP by only handling button structure and styling.
 *
 * Parameters
 * ----------
 * props : HeaderActionButtonProps
 *     Component props including href, tooltip, and children.
 */
export function HeaderActionButton({
  href,
  tooltipText,
  ariaLabel,
  children,
}: HeaderActionButtonProps) {
  return (
    <Tooltip text={tooltipText}>
      <Link
        href={href}
        className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-full border border-surface-a20 bg-surface-tonal-a10 transition-[colors,transform] duration-200 hover:bg-surface-tonal-a20 active:scale-[0.98]"
        aria-label={ariaLabel}
      >
        {children}
      </Link>
    </Tooltip>
  );
}
