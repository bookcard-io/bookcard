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

import { formatFileSize } from "@/utils/format";

/**
 * Book format data structure.
 */
export interface BookFormat {
  /** File format (e.g., 'EPUB', 'PDF'). */
  format: string;
  /** File size in bytes. */
  size: number;
}

/**
 * Props for FormatItem component.
 */
export interface FormatItemProps {
  /** Format data to display. */
  format: BookFormat;
  /** Action buttons to render. */
  actions?: React.ReactNode;
}

/**
 * Format item component for displaying a single book format.
 *
 * Displays format badge, details, and action buttons.
 * Follows OCP by accepting actions as children for extensibility.
 * Follows SRP by focusing solely on format item presentation.
 *
 * Parameters
 * ----------
 * props : FormatItemProps
 *     Component props including format data and actions.
 */
export function FormatItem({ format, actions }: FormatItemProps) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md border border-primary-a20 bg-surface-tonal-a10 p-3">
      <div className="flex h-10 w-10 min-w-10 items-center justify-center rounded-md border border-primary-a20 bg-surface-a20 font-semibold text-text-a0 text-xs">
        {format.format.toUpperCase()}
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <span className="font-semibold text-sm text-text-a0">
          {format.format.toUpperCase()}
        </span>
        <span className="text-sm text-text-a30">
          {formatFileSize(format.size)}
        </span>
      </div>
      <div className="flex gap-1">{actions}</div>
    </div>
  );
}
