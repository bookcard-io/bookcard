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
 * Defines the intended order of buttons in the header action bar.
 * Buttons are sorted by this order, with buttons not in this list appearing last.
 */
export const BUTTON_ORDER: readonly string[] = [
  "home",
  "admin",
  "profile",
] as const;

/**
 * Compares two button IDs for sorting based on their position in BUTTON_ORDER.
 *
 * Parameters
 * ----------
 * idA : string
 *     First button ID to compare.
 * idB : string
 *     Second button ID to compare.
 *
 * Returns
 * -------
 * number
 *     Negative if idA should come before idB, positive if after, 0 if equal.
 */
export function compareButtonOrder(idA: string, idB: string): number {
  const indexA = BUTTON_ORDER.indexOf(idA);
  const indexB = BUTTON_ORDER.indexOf(idB);

  // If both buttons are in the order list, sort by their position
  if (indexA >= 0 && indexB >= 0) {
    return indexA - indexB;
  }
  // If only A is in the order list, A comes first
  if (indexA >= 0) {
    return -1;
  }
  // If only B is in the order list, B comes first
  if (indexB >= 0) {
    return 1;
  }
  // If neither is in the order list, maintain original order
  return 0;
}
