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

import { useCallback } from "react";
import { useUser } from "@/contexts/UserContext";
import { updateDevice } from "@/services/deviceService";

export interface UseDeviceActionsResult {
  /** Set a device as the default device. */
  setDefaultDevice: (deviceId: number) => Promise<void>;
}

/**
 * Hook for managing device actions.
 *
 * Provides device-related operations using the device service.
 * Follows SRP by handling only device action logic.
 * Follows IOC by delegating to deviceService.
 *
 * Returns
 * -------
 * UseDeviceActionsResult
 *     Object containing device action functions.
 */
export function useDeviceActions(): UseDeviceActionsResult {
  const { user, updateUser, refresh: refreshUser } = useUser();

  const setDefaultDevice = useCallback(
    async (deviceId: number) => {
      // Find the device to get its current data
      const device = user?.ereader_devices?.find((d) => d.id === deviceId);
      if (!device) {
        return;
      }

      try {
        // Set device as default - update with current device data and is_default: true
        await updateDevice(deviceId, {
          email: device.email,
          device_name: device.device_name,
          device_type: device.device_type,
          preferred_format: device.preferred_format,
          is_default: true,
        });

        // Optimistically update user context
        if (user?.ereader_devices) {
          const updatedDevices = user.ereader_devices.map((d) =>
            d.id === deviceId
              ? { ...d, is_default: true }
              : { ...d, is_default: false },
          );
          updateUser({ ereader_devices: updatedDevices });
        }
      } catch (error) {
        // On error, refresh from server
        await refreshUser();
        // eslint-disable-next-line no-console
        console.error("Failed to set default device:", error);
      }
    },
    [user, updateUser, refreshUser],
  );

  return { setDefaultDevice };
}
