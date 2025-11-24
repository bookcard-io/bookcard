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
import { cn } from "@/libs/utils";

export interface HeaderButtonProps {
  /** Click handler for the button. */
  onClick?: () => void;
  /** Accessibility label. */
  ariaLabel: string;
  /** Icon or content to display. */
  children: ReactNode;
  /** Optional className. */
  className?: string;
}

/**
 * Reusable header action button component.
 *
 * Follows DRY by centralizing button styling and structure.
 * Follows SRP by focusing solely on button rendering.
 *
 * Parameters
 * ----------
 * props : HeaderButtonProps
 *     Button props including click handler and content.
 */
export function HeaderButton({
  onClick,
  ariaLabel,
  children,
  className,
}: HeaderButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex cursor-pointer items-center justify-center border-0 bg-transparent p-3 text-text-a40 transition-colors hover:text-text-a0",
        className,
      )}
      aria-label={ariaLabel}
    >
      {children}
    </button>
  );
}
