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

export interface TextCellProps {
  /** Text value to display. */
  value: string | null;
}

/**
 * Text cell component for displaying text values.
 *
 * Renders text with truncation and tooltip for long values.
 * Follows SRP by handling only text display logic.
 * Follows DRY by centralizing text cell rendering.
 *
 * Parameters
 * ----------
 * props : TextCellProps
 *     Component props including text value.
 */
export function TextCell({ value }: TextCellProps) {
  if (value === null) {
    return <span className="text-text-a40">—</span>;
  }

  return (
    <span className="truncate" title={value}>
      {value}
    </span>
  );
}
