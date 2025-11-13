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

import { Button } from "@/components/forms/Button";

export interface BookCoverActionsProps {
  /** Whether URL input is visible. */
  isUrlInputVisible: boolean;
  /** Handler for "Set cover from URL" button click. */
  onSetFromUrlClick: () => void;
  /** URL input component to render when visible. */
  urlInput?: React.ReactNode;
}

/**
 * Book cover actions component.
 *
 * Displays action buttons for cover operations.
 * Follows SRP by focusing solely on cover action buttons.
 *
 * Parameters
 * ----------
 * props : BookCoverActionsProps
 *     Component props including handlers and URL input.
 */
export function BookCoverActions({
  isUrlInputVisible,
  onSetFromUrlClick,
  urlInput,
}: BookCoverActionsProps) {
  return (
    <div className="flex flex-col gap-2">
      <Button
        type="button"
        variant="ghost"
        size="small"
        className="!border-primary-a20 !text-primary-a20 hover:!text-primary-a20 focus:!shadow-none w-full justify-start rounded-lg hover:border-primary-a10 hover:bg-surface-a20 focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2"
      >
        <span
          className="pi pi-image mr-2 text-primary-a20"
          aria-hidden="true"
        />
        Select cover
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="small"
        className="!border-primary-a20 !text-primary-a20 hover:!text-primary-a20 focus:!shadow-none w-full justify-start rounded-lg hover:border-primary-a10 hover:bg-surface-a20 focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2"
        onClick={onSetFromUrlClick}
      >
        <span className="pi pi-link mr-2 text-primary-a20" aria-hidden="true" />
        Set cover from URL
      </Button>
      {isUrlInputVisible && urlInput}
      <Button
        type="button"
        variant="ghost"
        size="small"
        className="!border-primary-a20 !text-primary-a20 hover:!text-primary-a20 focus:!shadow-none w-full justify-start rounded-lg hover:border-primary-a10 hover:bg-surface-a20 focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2"
      >
        <span
          className="pi pi-download mr-2 text-primary-a20"
          aria-hidden="true"
        />
        Download cover
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="small"
        className="!border-primary-a20 !text-primary-a20 hover:!text-primary-a20 focus:!shadow-none w-full justify-start rounded-lg hover:border-primary-a10 hover:bg-surface-a20 focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2"
      >
        <span
          className="pi pi-sparkles mr-2 text-primary-a20"
          aria-hidden="true"
        />
        Generate cover
      </Button>
    </div>
  );
}
