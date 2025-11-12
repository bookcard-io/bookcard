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

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge class names with Tailwind class conflict resolution.
 *
 * Combines clsx for conditional classes and tailwind-merge to resolve
 * Tailwind class conflicts (e.g., "p-4 p-2" becomes "p-2").
 *
 * Parameters
 * ----------
 * ...inputs : ClassValue[]
 *     Class names to merge (strings, objects, arrays, etc.).
 *
 * Returns
 * -------
 * string
 *     Merged class name string.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
