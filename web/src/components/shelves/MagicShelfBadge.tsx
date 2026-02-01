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

import { FaWandMagicSparkles } from "react-icons/fa6";
import { cn } from "@/libs/utils";

export interface MagicShelfBadgeProps {
  /** Optional className override. */
  className?: string;
}

/**
 * Visual indicator for Magic Shelves.
 *
 * Extracted from `ShelfCard` to keep shelf-type decorations reusable and
 * maintainable (SRP/DRY).
 */
export function MagicShelfBadge({ className }: MagicShelfBadgeProps) {
  return (
    <div
      className={cn(
        "pointer-events-none absolute top-2 right-2 z-20",
        "flex h-7 w-7 items-center justify-center rounded-full",
        "bg-surface-a0/50 text-warning-a10 backdrop-blur-sm",
        className,
      )}
      title="Magic shelf"
      aria-hidden="true"
      data-magic-shelf-icon
    >
      <FaWandMagicSparkles className="h-4 w-4" />
    </div>
  );
}
