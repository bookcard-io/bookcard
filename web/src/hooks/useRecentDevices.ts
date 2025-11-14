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

import { useMemo } from "react";
import type { EReaderDevice } from "@/contexts/UserContext";

export interface UseRecentDevicesOptions {
  /** Maximum number of devices to return (default: 3). */
  limit?: number;
}

/**
 * Hook for getting recently created devices.
 *
 * Returns the most recently created devices sorted by id (as proxy for created_at).
 * Follows SRP by handling only device sorting and filtering.
 * Follows DRY by centralizing the recent devices calculation logic.
 *
 * Parameters
 * ----------
 * devices : EReaderDevice[]
 *     Full list of devices to filter and sort.
 * options : UseRecentDevicesOptions
 *     Configuration options.
 *
 * Returns
 * -------
 * EReaderDevice[]
 *     Top N most recently created devices (most recent first).
 */
export function useRecentDevices(
  devices: EReaderDevice[] | undefined,
  options: UseRecentDevicesOptions = {},
): EReaderDevice[] {
  const { limit = 3 } = options;

  return useMemo(() => {
    const deviceList = devices || [];
    // Sort by id descending (newer devices typically have higher ids)
    // Since created_at might not be in the interface, we use id as fallback
    const sorted = [...deviceList].sort((a, b) => b.id - a.id);
    return sorted.slice(0, limit);
  }, [devices, limit]);
}
