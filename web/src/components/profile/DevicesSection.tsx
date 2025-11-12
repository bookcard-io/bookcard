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

import type { EReaderDevice } from "./hooks/useUserProfile";

interface DevicesSectionProps {
  devices: EReaderDevice[] | undefined;
}

/**
 * Devices section displaying user's e-reader devices.
 *
 * Shows a table of devices with ability to manage them (no-op for now).
 * Follows SRP by handling only device display and management UI.
 */
export function DevicesSection({ devices }: DevicesSectionProps) {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="m-0 font-semibold text-text-a0 text-xl">My Devices</h2>
        <button
          type="button"
          onClick={() => {
            // No-op for now
          }}
          className="rounded border-0 bg-primary-a0 px-4 py-2 font-medium text-sm text-text-a0 transition-colors duration-200 hover:bg-primary-a10 focus:outline-none focus:ring-2 focus:ring-primary-a0 active:bg-primary-a20 disabled:cursor-not-allowed disabled:bg-surface-tonal-a20 disabled:text-text-a30"
        >
          Manage Devices
        </button>
      </div>

      <div className="rounded border border-surface-a20">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-surface-a20 border-b bg-surface-tonal-a10">
                <th className="px-4 py-3 text-left font-medium text-sm text-text-a20">
                  Device Name
                </th>
                <th className="px-4 py-3 text-left font-medium text-sm text-text-a20">
                  Email
                </th>
                <th className="px-4 py-3 text-left font-medium text-sm text-text-a20">
                  Type
                </th>
                <th className="px-4 py-3 text-left font-medium text-sm text-text-a20">
                  Format
                </th>
                <th className="px-4 py-3 text-left font-medium text-sm text-text-a20">
                  Default
                </th>
              </tr>
            </thead>
            <tbody>
              {!devices || devices.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="px-4 py-8 text-center text-text-a30"
                  >
                    No devices configured
                  </td>
                </tr>
              ) : (
                devices.map((device) => (
                  <tr
                    key={device.id}
                    className="border-surface-a20 border-b transition-colors duration-150 last:border-b-0 hover:bg-surface-tonal-a10"
                  >
                    <td className="px-4 py-3 text-text-a0">
                      {device.device_name || (
                        <span className="text-text-a30">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-text-a0">{device.email}</td>
                    <td className="px-4 py-3 text-text-a0 capitalize">
                      {device.device_type}
                    </td>
                    <td className="px-4 py-3 text-text-a0 uppercase">
                      {device.preferred_format || (
                        <span className="text-text-a30">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-text-a0">
                      {device.is_default ? (
                        <span className="rounded bg-primary-a0/20 px-2 py-1 font-medium text-primary-a0 text-xs">
                          Default
                        </span>
                      ) : (
                        <span className="text-text-a30">—</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
