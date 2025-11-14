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
 * Get display name for a device.
 *
 * Returns device_name if available, otherwise falls back to email.
 * Follows SRP by handling only device name formatting.
 *
 * Parameters
 * ----------
 * device : EReaderDevice
 *     Device to get display name for.
 *
 * Returns
 * -------
 * string
 *     Display name for the device.
 */
export function getDeviceDisplayName(device: EReaderDevice): string {
  return device.device_name || device.email;
}
