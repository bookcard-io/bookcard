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

export interface CreateShelfCardProps {
  /** Callback when create shelf card is clicked. */
  onClick: () => void;
}

/**
 * Create shelf card component.
 *
 * Displays a card for creating a new shelf in the grid.
 * Follows SRP by focusing solely on create shelf presentation.
 * Follows IOC by accepting callback for click action.
 *
 * Parameters
 * ----------
 * props : CreateShelfCardProps
 *     Component props.
 */
export function CreateShelfCard({ onClick }: CreateShelfCardProps) {
  const handleKeyDown = createEnterSpaceHandler(onClick);

  return (
    <button
      type="button"
      className={cn(
        "group flex cursor-pointer flex-col overflow-hidden rounded",
        "w-full max-w-[200px] border-2 border-surface-a30 border-dashed bg-gradient-to-b from-surface-a0 to-surface-a10 p-0 text-left",
        "transition-[transform,box-shadow,border-color] duration-200 ease-out",
        "hover:-translate-y-0.5 hover:border-primary-a0 hover:shadow-card-hover",
        "focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2",
        "focus:not-focus-visible:outline-none focus:outline-none",
      )}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      aria-label="Create new shelf"
    >
      <div className="relative aspect-[2/3] w-full overflow-hidden">
        <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-surface-a20 to-surface-a10">
          <i
            className="pi pi-plus text-4xl text-text-a30 transition-colors duration-200 group-hover:text-primary-a0"
            aria-hidden="true"
          />
        </div>
      </div>
      <div className="flex min-h-16 flex-col gap-1 bg-surface-a10 p-[0.75rem]">
        <h3 className="m-0 line-clamp-2 font-[500] text-[0.875rem] text-text-a30 leading-[1.3]">
          Create shelf
        </h3>
      </div>
    </button>
  );
}
