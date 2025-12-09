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

import { cn } from "@/libs/utils";
import type { ShelfType } from "@/types/shelf";

export interface ReadListBadgeProps {
  /** Shelf type. */
  shelfType: ShelfType;
  /** Additional CSS classes. */
  className?: string;
}

/**
 * Badge component to display read list indicator.
 *
 * Shows a badge when shelf_type is "read_list" to distinguish
 * read lists from regular shelves.
 */
export function ReadListBadge({ shelfType, className }: ReadListBadgeProps) {
  if (shelfType !== "read_list") {
    return null;
  }

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full bg-primary-a10 px-2 py-0.5 font-medium text-primary-a90 text-xs",
        className,
      )}
    >
      Read List
    </span>
  );
}
