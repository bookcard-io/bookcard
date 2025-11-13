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

import { formatDate } from "@/utils/format";

export interface DateCellProps {
  /** Date value to display. */
  value: string | null;
}

/**
 * Date cell component for displaying formatted dates.
 *
 * Formats and displays date values consistently.
 * Follows SRP by handling only date formatting and display.
 * Follows DRY by centralizing date formatting logic.
 *
 * Parameters
 * ----------
 * props : DateCellProps
 *     Component props including date value.
 */
export function DateCell({ value }: DateCellProps) {
  if (value === null) {
    return <span className="text-text-a40">—</span>;
  }

  return <span>{formatDate(value)}</span>;
}
