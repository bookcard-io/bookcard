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
 * Service for interacting with device API endpoints.
 *
 * Provides methods for creating e-reader devices.
 */

import type { EReaderDevice } from "@/components/profile/hooks/useUserProfile";

export interface DeviceCreate {
  email: string;
  device_name?: string | null;
  device_type?: string;
  preferred_format?: string | null;
  is_default?: boolean;
}

export interface DeviceUpdate {
  email: string;
  device_name?: string | null;
  device_type?: string;
  preferred_format?: string | null;
  is_default?: boolean;
}

const API_BASE = "/api/devices";

/**
 * Create a new device.
 *
 * Parameters
 * ----------
 * data : DeviceCreate
 *     Device creation data.
 *
 * Returns
 * -------
 * Promise<EReaderDevice>
 *     Created device data.
 */
export async function createDevice(data: DeviceCreate): Promise<EReaderDevice> {
  const response = await fetch(API_BASE, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to create device" }));
    throw new Error(error.detail || "Failed to create device");
  }

  return response.json();
}

/**
 * Update a device.
 *
 * Parameters
 * ----------
 * deviceId : number
 *     Device ID to update.
 * data : DeviceUpdate
 *     Device update data.
 *
 * Returns
 * -------
 * Promise<EReaderDevice>
 *     Updated device data.
 */
export async function updateDevice(
  deviceId: number,
  data: DeviceUpdate,
): Promise<EReaderDevice> {
  const response = await fetch(`${API_BASE}/${deviceId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to update device" }));
    throw new Error(error.detail || "Failed to update device");
  }

  return response.json();
}

/**
 * Delete a device.
 *
 * Parameters
 * ----------
 * deviceId : number
 *     Device ID to delete.
 *
 * Returns
 * -------
 * Promise<void>
 */
export async function deleteDevice(deviceId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/${deviceId}`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to delete device" }));
    throw new Error(error.detail || "Failed to delete device");
  }
}
