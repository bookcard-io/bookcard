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

import { useState } from "react";
import { useUser } from "@/contexts/UserContext";
import { cn } from "@/libs/utils";
import {
  createDevice,
  deleteDevice,
  updateDevice,
} from "@/services/deviceService";
import { AddDeviceCard } from "./AddDeviceCard";
import { DeviceCard } from "./DeviceCard";
import { DeviceEditModal } from "./DeviceEditModal";
import type { EReaderDevice } from "./hooks/useUserProfile";

interface DevicesSectionProps {
  devices: EReaderDevice[] | undefined;
}

/**
 * Devices section displaying user's e-reader devices.
 *
 * Shows a grid of device cards with ability to manage them (no-op for now).
 * Follows SRP by handling only device display and management UI.
 * Follows DRY by reusing ShelvesGrid layout pattern.
 */
export function DevicesSection({ devices }: DevicesSectionProps) {
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingDevice, setEditingDevice] = useState<EReaderDevice | null>(
    null,
  );
  const { refresh, updateUser, user } = useUser();

  const deviceList = devices || [];

  const handleCreateDevice = async (data: {
    email: string;
    device_name?: string | null;
    device_type?: string;
    preferred_format?: string | null;
    is_default?: boolean;
  }) => {
    const newDevice = await createDevice(data);

    // Optimistically update devices in user context.
    // If the new device is default, clear the default flag on all others
    // so only one card shows the asterisk immediately.
    const isNewDefault = Boolean(data.is_default);

    if (user) {
      const existingDevices = user.ereader_devices ?? [];

      const normalizedNewDevice: EReaderDevice = {
        ...newDevice,
        // Ensure the new device reflects the default choice immediately
        is_default: isNewDefault ? true : newDevice.is_default,
      };

      const clearedDefaults = isNewDefault
        ? existingDevices.map((device) => ({
            ...device,
            is_default: false,
          }))
        : existingDevices;

      const updatedDevices = [...clearedDefaults, normalizedNewDevice];
      updateUser({ ereader_devices: updatedDevices });
    }

    // UI already updated optimistically, no need to refresh
    return newDevice;
  };

  const handleUpdateDevice = async (data: {
    email: string;
    device_name?: string | null;
    device_type?: string;
    preferred_format?: string | null;
    is_default?: boolean;
  }) => {
    if (!editingDevice) {
      throw new Error("No device to update");
    }

    const updatedDevice = await updateDevice(editingDevice.id, data);

    // Optimistically update device in user context
    const isNewDefault = Boolean(data.is_default);

    if (user) {
      const existingDevices = user.ereader_devices ?? [];

      const normalizedUpdatedDevice: EReaderDevice = {
        ...updatedDevice,
        is_default: isNewDefault ? true : updatedDevice.is_default,
      };

      // If setting as default, clear default flag on all other devices
      const clearedDefaults = isNewDefault
        ? existingDevices.map((device) =>
            device.id === editingDevice.id
              ? normalizedUpdatedDevice
              : { ...device, is_default: false },
          )
        : existingDevices.map((device) =>
            device.id === editingDevice.id ? normalizedUpdatedDevice : device,
          );

      updateUser({ ereader_devices: clearedDefaults });
    }

    return updatedDevice;
  };

  const handleDeleteDevice = async (deviceId: number) => {
    // Optimistically remove device from UI immediately
    if (user?.ereader_devices) {
      const updatedDevices = user.ereader_devices.filter(
        (d) => d.id !== deviceId,
      );
      updateUser({ ereader_devices: updatedDevices });
    }

    try {
      await deleteDevice(deviceId);
      // UI already updated optimistically, no need to refresh
    } catch (error) {
      // On error, revert by refreshing from server
      await refresh();
      throw error;
    }
  };

  return (
    <div id="manage-devices" className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2
          className={cn(
            /* Layout */
            "m-0",
            /* Typography */
            "font-semibold text-text-a0 text-xl",
          )}
        >
          My Devices
        </h2>
      </div>
      <p className="text-sm text-text-a60">
        Devices are used for sending books via email (e.g., Send to Kindle). You
        can add multiple devices and set a default. All send-to and email
        features require a device with an email address.
      </p>

      <div className="w-full">
        {deviceList.length > 0 && (
          <div className="pb-4 text-left text-sm text-text-a40">
            {deviceList.length} {deviceList.length === 1 ? "device" : "devices"}
          </div>
        )}
        <div
          className={cn(
            /* Layout */
            "grid justify-items-start gap-4",
            /* Grid columns */
            "grid-cols-[repeat(auto-fit,minmax(110px,175px))]",
            "md:grid-cols-[repeat(auto-fit,minmax(110px,175px))] md:gap-4",
            "lg:grid-cols-[repeat(auto-fit,minmax(110px,175px))]",
          )}
        >
          {deviceList.map((device) => (
            <DeviceCard
              key={device.id}
              device={device}
              onEdit={(device) => setEditingDevice(device)}
              onDelete={handleDeleteDevice}
            />
          ))}
          {/* Always show "Add device" card as the last item */}
          <AddDeviceCard onClick={() => setShowAddModal(true)} />
        </div>
      </div>
      {showAddModal && (
        <DeviceEditModal
          onClose={() => setShowAddModal(false)}
          onSave={handleCreateDevice}
        />
      )}
      {editingDevice && (
        <DeviceEditModal
          device={editingDevice}
          onClose={() => setEditingDevice(null)}
          onSave={handleUpdateDevice}
        />
      )}
    </div>
  );
}
