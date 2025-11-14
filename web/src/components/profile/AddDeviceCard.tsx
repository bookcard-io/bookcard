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

export interface AddDeviceCardProps {
  /** Callback when add device card is clicked. */
  onClick: () => void;
}

/**
 * Add device card component.
 *
 * Displays a card for adding a new device in the grid.
 * Follows SRP by focusing solely on add device presentation.
 * Follows IOC by accepting callback for click action.
 *
 * Parameters
 * ----------
 * props : AddDeviceCardProps
 *     Component props.
 */
export function AddDeviceCard({ onClick }: AddDeviceCardProps) {
  const handleKeyDown = createEnterSpaceHandler(onClick);

  return (
    <button
      type="button"
      className={cn(
        /* Layout */
        "group flex cursor-pointer flex-col overflow-hidden rounded text-left",
        "w-full max-w-[120px] p-0",
        /* Border & background */
        "border-2 border-surface-a30 border-dashed",
        "bg-gradient-to-b from-surface-a0 to-surface-a10",
        /* Interactions */
        "transition-[transform,box-shadow,border-color] duration-200 ease-out",
        "hover:-translate-y-0.5 hover:border-primary-a0 hover:shadow-card-hover",
        /* Focus states */
        "focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2",
        "focus:not-focus-visible:outline-none focus:outline-none",
      )}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      aria-label="Add new device"
    >
      <div
        className={cn(
          /* Layout */
          "relative aspect-[2/3] w-full overflow-hidden",
        )}
      >
        <div
          className={cn(
            /* Layout */
            "flex h-full w-full items-center justify-center",
            /* Background */
            "bg-gradient-to-br from-surface-a20 to-surface-a10",
          )}
        >
          <i
            className={cn(
              /* Icon */
              "pi pi-plus text-2xl text-text-a30",
              /* Interactions */
              "transition-colors duration-200",
              "group-hover:text-primary-a0",
            )}
            aria-hidden="true"
          />
        </div>
      </div>
      <div
        className={cn(
          /* Layout */
          "flex min-h-12 flex-col gap-0.5",
          /* Background */
          "bg-surface-a10 p-2",
        )}
      >
        <h3
          className={cn(
            /* Layout */
            "m-0 line-clamp-2",
            /* Typography */
            "font-[500] text-text-a30 text-xs leading-[1.2]",
          )}
        >
          Add device
        </h3>
      </div>
    </button>
  );
}
