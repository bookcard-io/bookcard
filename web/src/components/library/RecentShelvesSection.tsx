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

import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";
import { useUser } from "@/contexts/UserContext";
import { cn } from "@/libs/utils";
import type { Shelf } from "@/types/shelf";

export interface RecentShelvesSectionProps {
  /** List of recent shelves to display. */
  shelves: Shelf[];
  /** Callback when a shelf is clicked. */
  onShelfClick: (shelfId: number) => void;
  /** Whether actions are disabled. */
  disabled?: boolean;
}

/**
 * Recent shelves section component.
 *
 * Displays a divider and list of recent shelves in a menu.
 * Follows SRP by handling only recent shelves display.
 * Uses IOC via callback props for interactions.
 *
 * Parameters
 * ----------
 * props : RecentShelvesSectionProps
 *     Component props including shelves list and callbacks.
 */
export function RecentShelvesSection({
  shelves,
  onShelfClick,
  disabled = false,
}: RecentShelvesSectionProps) {
  const { canPerformAction } = useUser();
  const canEditShelves = canPerformAction("shelves", "edit");

  if (shelves.length === 0) {
    return null;
  }

  return (
    <>
      <hr className={cn("my-1 h-px border-0 bg-surface-tonal-a20")} />
      <div
        className="px-4 py-1.5 font-medium text-xs uppercase"
        style={{ color: "var(--color-surface-tonal-a50)" }}
      >
        Recent
      </div>
      {shelves.map((shelf) => (
        <DropdownMenuItem
          key={shelf.id}
          label={shelf.name}
          onClick={canEditShelves ? () => onShelfClick(shelf.id) : undefined}
          disabled={!canEditShelves || disabled}
        />
      ))}
    </>
  );
}
