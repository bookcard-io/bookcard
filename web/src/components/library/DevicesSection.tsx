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

import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";
import type { EReaderDevice } from "@/contexts/UserContext";
import { cn } from "@/libs/utils";

export interface DevicesSectionProps {
  /** List of devices to display. */
  devices: EReaderDevice[];
  /** Callback when a device is clicked. */
  onDeviceClick: (device: EReaderDevice) => void;
  /** Whether actions are disabled. */
  disabled?: boolean;
}

/**
 * Devices section component.
 *
 * Displays a divider and list of devices in a menu.
 * Follows SRP by handling only devices display.
 * Uses IOC via callback props for interactions.
 *
 * Parameters
 * ----------
 * props : DevicesSectionProps
 *     Component props including devices list and callbacks.
 */
export function DevicesSection({
  devices,
  onDeviceClick,
  disabled = false,
}: DevicesSectionProps) {
  if (devices.length === 0) {
    return null;
  }

  return (
    <>
      <hr className={cn("my-1 h-px border-0 bg-surface-tonal-a20")} />
      <div
        className="px-4 py-1.5 font-medium text-xs uppercase"
        style={{ color: "var(--color-surface-tonal-a50)" }}
      >
        Devices
      </div>
      {devices.map((device) => (
        <DropdownMenuItem
          key={device.id}
          label={device.device_name || device.email}
          onClick={() => onDeviceClick(device)}
          disabled={disabled}
        />
      ))}
    </>
  );
}
