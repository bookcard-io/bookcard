// Copyright (C) 2025 khoa and others
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

import { TextColumnOne24Regular } from "@/icons/TextColumnOne24Regular";
import { TextColumnTwo24Regular } from "@/icons/TextColumnTwo24Regular";
import { cn } from "@/libs/utils";

export type PageLayout = "single" | "two-column";

export interface LayoutSelectorProps {
  /** Currently selected layout. */
  selectedLayout: PageLayout;
  /** Callback when layout changes. */
  onLayoutChange: (layout: PageLayout) => void;
}

/**
 * Page layout selector component.
 *
 * Displays single-column and two-column layout options with icons.
 * Follows SRP by handling only layout selection UI.
 * Follows IOC by accepting callbacks as props.
 *
 * Parameters
 * ----------
 * props : LayoutSelectorProps
 *     Component props including selected layout and change handler.
 */
export function LayoutSelector({
  selectedLayout,
  onLayoutChange,
}: LayoutSelectorProps) {
  return (
    <div className="mb-8">
      <h3 className="mb-4 font-medium text-sm text-text-a0">Layout</h3>
      <div className="grid grid-cols-3 gap-3">
        <button
          type="button"
          onClick={() => onLayoutChange("two-column")}
          className={cn(
            "flex flex-col items-center gap-2 rounded-md border p-2 transition-colors",
            selectedLayout === "two-column"
              ? "border-primary-a0 bg-primary-a0/10"
              : "border-surface-a20 bg-surface-a10 hover:border-surface-a30 hover:bg-surface-a20",
          )}
          aria-label="Select two column layout"
          aria-pressed={selectedLayout === "two-column"}
        >
          <div
            className={cn(
              "flex h-12 w-12 items-center justify-center rounded border text-3xl",
              selectedLayout === "two-column"
                ? "border-primary-a0 bg-primary-a0/20 text-primary-a0"
                : "border-surface-a30 bg-surface-a20 text-text-a40",
            )}
          >
            <TextColumnTwo24Regular className="h-6 w-6" />
          </div>
          <span
            className={cn(
              "text-xs",
              selectedLayout === "two-column"
                ? "text-primary-a0"
                : "text-text-a40",
            )}
          >
            Two Column
          </span>
        </button>
        <button
          type="button"
          onClick={() => onLayoutChange("single")}
          className={cn(
            "flex flex-col items-center gap-2 rounded-md border p-2 transition-colors",
            selectedLayout === "single"
              ? "border-primary-a0 bg-primary-a0/10"
              : "border-surface-a20 bg-surface-a10 hover:border-surface-a30 hover:bg-surface-a20",
          )}
          aria-label="Select single column layout"
          aria-pressed={selectedLayout === "single"}
        >
          <div
            className={cn(
              "flex h-12 w-12 items-center justify-center rounded border text-3xl",
              selectedLayout === "single"
                ? "border-primary-a0 bg-primary-a0/20 text-primary-a0"
                : "border-surface-a30 bg-surface-a20 text-text-a40",
            )}
          >
            <TextColumnOne24Regular className="h-6 w-6" />
          </div>
          <span
            className={cn(
              "text-xs",
              selectedLayout === "single" ? "text-primary-a0" : "text-text-a40",
            )}
          >
            Single
          </span>
        </button>
      </div>
    </div>
  );
}
