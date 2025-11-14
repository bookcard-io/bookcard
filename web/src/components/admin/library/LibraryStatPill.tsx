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

/**
 * Single library statistic pill component.
 *
 * Renders a single pill badge for a statistic.
 * Follows SRP by focusing solely on individual pill rendering.
 */

export interface LibraryStatPillProps {
  /** Formatted value to display. */
  value: string;
  /** Label to display (e.g., "BOOKS"). */
  label: string;
}

/**
 * Library statistic pill component.
 *
 * Renders a single rounded pill badge with value and label.
 *
 * Parameters
 * ----------
 * props : LibraryStatPillProps
 *     Component props including value and label.
 */
export function LibraryStatPill({ value, label }: LibraryStatPillProps) {
  return (
    <div className="rounded-full bg-[var(--color-info-a10)] px-2.5 py-1 font-medium text-[var(--color-white)] text-xs">
      {value} {label}
    </div>
  );
}
