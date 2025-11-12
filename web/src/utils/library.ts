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

import type { Library } from "@/components/admin/library/types";

/**
 * Generate a default library name based on existing libraries.
 *
 * Follows the pattern "My Library" or "My Library (N)" where N is the next
 * available number. If "My Library" exists, uses numbered variants.
 * Follows SRP by focusing solely on name generation logic.
 *
 * Parameters
 * ----------
 * existingLibraries : Library[]
 *     List of existing libraries to check for name conflicts.
 * providedName : string
 *     Optional name provided by the user.
 *
 * Returns
 * -------
 * string
 *     Generated or provided library name.
 */
export function generateLibraryName(
  existingLibraries: Library[],
  providedName?: string,
): string {
  const trimmedName = providedName?.trim();
  if (trimmedName) {
    return trimmedName;
  }

  const myLibraryPattern = /^My Library(?: \((\d+)\))?$/;
  const hasBaseName = existingLibraries.some(
    (lib) => lib.name === "My Library",
  );
  const numberedNames = existingLibraries
    .map((lib) => {
      const match = lib.name.match(myLibraryPattern);
      return match?.[1] ? parseInt(match[1], 10) : null;
    })
    .filter((num): num is number => num !== null);

  if (!hasBaseName && numberedNames.length === 0) {
    return "My Library";
  }

  // Find the next available number
  const maxNumber = numberedNames.length > 0 ? Math.max(...numberedNames) : 0;
  return `My Library (${maxNumber + 1})`;
}
