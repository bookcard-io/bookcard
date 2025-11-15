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

import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import type { EReaderDevice } from "@/contexts/UserContext";
import { useRecentDevices } from "./useRecentDevices";

/**
 * Creates a mock e-reader device.
 *
 * Parameters
 * ----------
 * id : number
 *     Device ID.
 * overrides : Partial<EReaderDevice>
 *     Optional overrides for default values.
 *
 * Returns
 * -------
 * EReaderDevice
 *     Mock device object.
 */
function createMockDevice(
  id: number,
  overrides: Partial<EReaderDevice> = {},
): EReaderDevice {
  return {
    id,
    user_id: 1,
    email: `device${id}@example.com`,
    device_name: `Device ${id}`,
    device_type: "kindle",
    preferred_format: "epub",
    is_default: false,
    ...overrides,
  };
}

describe("useRecentDevices", () => {
  beforeEach(() => {
    // No setup needed
  });

  it("should return empty array when devices is undefined", () => {
    const { result } = renderHook(() => useRecentDevices(undefined));

    expect(result.current).toEqual([]);
  });

  it("should return empty array when devices is empty", () => {
    const { result } = renderHook(() => useRecentDevices([]));

    expect(result.current).toEqual([]);
  });

  it("should return devices sorted by id descending", () => {
    const devices = [
      createMockDevice(1),
      createMockDevice(3),
      createMockDevice(2),
      createMockDevice(5),
      createMockDevice(4),
    ];

    const { result } = renderHook(() => useRecentDevices(devices));

    expect(result.current).toHaveLength(3); // Default limit is 3
    expect(result.current[0]?.id).toBe(5);
    expect(result.current[1]?.id).toBe(4);
    expect(result.current[2]?.id).toBe(3);
  });

  it("should respect custom limit", () => {
    const devices = [
      createMockDevice(1),
      createMockDevice(2),
      createMockDevice(3),
      createMockDevice(4),
      createMockDevice(5),
    ];

    const { result } = renderHook(() =>
      useRecentDevices(devices, { limit: 2 }),
    );

    expect(result.current).toHaveLength(2);
    expect(result.current[0]?.id).toBe(5);
    expect(result.current[1]?.id).toBe(4);
  });

  it("should return all devices when limit exceeds device count", () => {
    const devices = [createMockDevice(1), createMockDevice(2)];

    const { result } = renderHook(() =>
      useRecentDevices(devices, { limit: 10 }),
    );

    expect(result.current).toHaveLength(2);
    expect(result.current[0]?.id).toBe(2);
    expect(result.current[1]?.id).toBe(1);
  });

  it("should use default limit of 3", () => {
    const devices = [
      createMockDevice(1),
      createMockDevice(2),
      createMockDevice(3),
      createMockDevice(4),
    ];

    const { result } = renderHook(() => useRecentDevices(devices));

    expect(result.current).toHaveLength(3);
  });
});
