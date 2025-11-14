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

import type { EReaderDevice } from "@/contexts/UserContext";

/**
 * Generate a default device name based on existing devices.
 *
 * Follows the pattern "My Kindle" or "My Kindle (N)" where N is the next
 * available number. If "My Kindle" exists, uses numbered variants.
 * Follows SRP by focusing solely on name generation logic.
 *
 * Parameters
 * ----------
 * existingDevices : EReaderDevice[]
 *     List of existing devices to check for name conflicts.
 * providedName : string
 *     Optional name provided by the user.
 *
 * Returns
 * -------
 * string
 *     Generated or provided device name.
 */
export function generateDeviceName(
  existingDevices: EReaderDevice[],
  providedName?: string,
): string {
  const trimmedName = providedName?.trim();
  if (trimmedName) {
    return trimmedName;
  }

  const myKindlePattern = /^My Kindle(?: \((\d+)\))?$/;
  const hasBaseName = existingDevices.some(
    (device) => device.device_name === "My Kindle",
  );
  const numberedNames = existingDevices
    .map((device) => {
      const match = device.device_name?.match(myKindlePattern);
      return match?.[1] ? parseInt(match[1], 10) : null;
    })
    .filter((num): num is number => num !== null);

  if (!hasBaseName && numberedNames.length === 0) {
    return "My Kindle";
  }

  // Find the next available number
  const maxNumber = numberedNames.length > 0 ? Math.max(...numberedNames) : 0;
  return `My Kindle (${maxNumber + 1})`;
}
