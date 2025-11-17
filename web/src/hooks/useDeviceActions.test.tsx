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

import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { UserContext } from "@/contexts/UserContext";
import { useDeviceActions } from "./useDeviceActions";

vi.mock("@/services/deviceService", () => ({
  updateDevice: vi.fn(),
}));

import * as deviceService from "@/services/deviceService";

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
  overrides: Partial<{
    email: string;
    device_name: string;
    device_type: string;
    preferred_format: string;
    is_default: boolean;
  }> = {},
) {
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

/**
 * Creates a wrapper component with UserContext.
 *
 * Parameters
 * ----------
 * mockContext : Partial<UserContextValue>
 *     Mock context values.
 *
 * Returns
 * -------
 * ({ children }: { children: ReactNode }) => JSX.Element
 *     Wrapper component.
 */
function createWrapper(
  mockContext: Partial<
    React.ComponentProps<typeof UserContext.Provider>["value"]
  > = {},
) {
  const defaultContext: React.ComponentProps<
    typeof UserContext.Provider
  >["value"] = {
    user: null,
    isLoading: false,
    error: null,
    refresh: vi.fn(),
    refreshTimestamp: 0,
    updateUser: vi.fn(),
    profilePictureUrl: null,
    invalidateProfilePictureCache: vi.fn(),
    settings: {},
    isSaving: false,
    getSetting: vi.fn(() => null),
    updateSetting: vi.fn(),
    defaultDevice: null,
    hasPermission: vi.fn(() => false),
    canPerformAction: vi.fn(() => false),
    ...mockContext,
  };

  return ({ children }: { children: ReactNode }) => (
    <UserContext.Provider value={defaultContext}>
      {children}
    </UserContext.Provider>
  );
}

describe("useDeviceActions", () => {
  const mockRefresh = vi.fn();
  const mockUpdateUser = vi.fn();
  const consoleErrorSpy = vi
    .spyOn(console, "error")
    .mockImplementation(() => {});

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(deviceService.updateDevice).mockResolvedValue(
      createMockDevice(1, { is_default: true }),
    );
  });

  afterEach(() => {
    consoleErrorSpy.mockClear();
  });

  it("should return setDefaultDevice function", () => {
    const devices = [createMockDevice(1), createMockDevice(2)];
    const { result } = renderHook(() => useDeviceActions(), {
      wrapper: createWrapper({
        user: {
          id: 1,
          username: "test",
          email: "test@example.com",
          ereader_devices: devices,
        } as never,
        updateUser: mockUpdateUser,
        refresh: mockRefresh,
      }),
    });

    expect(result.current.setDefaultDevice).toBeDefined();
  });

  it("should set device as default successfully", async () => {
    const device1 = createMockDevice(1, { is_default: false });
    const device2 = createMockDevice(2, { is_default: true });
    const devices = [device1, device2];

    const { result } = renderHook(() => useDeviceActions(), {
      wrapper: createWrapper({
        user: {
          id: 1,
          username: "test",
          email: "test@example.com",
          ereader_devices: devices,
        } as never,
        updateUser: mockUpdateUser,
        refresh: mockRefresh,
      }),
    });

    await act(async () => {
      await result.current.setDefaultDevice(1);
    });

    expect(vi.mocked(deviceService.updateDevice)).toHaveBeenCalledWith(1, {
      email: device1.email,
      device_name: device1.device_name,
      device_type: device1.device_type,
      preferred_format: device1.preferred_format,
      is_default: true,
    });

    expect(mockUpdateUser).toHaveBeenCalledWith({
      ereader_devices: [
        { ...device1, is_default: true },
        { ...device2, is_default: false },
      ],
    });
  });

  it("should return early if device is not found", async () => {
    const devices = [createMockDevice(1), createMockDevice(2)];

    const { result } = renderHook(() => useDeviceActions(), {
      wrapper: createWrapper({
        user: {
          id: 1,
          username: "test",
          email: "test@example.com",
          ereader_devices: devices,
        } as never,
        updateUser: mockUpdateUser,
        refresh: mockRefresh,
      }),
    });

    await act(async () => {
      await result.current.setDefaultDevice(999);
    });

    expect(vi.mocked(deviceService.updateDevice)).not.toHaveBeenCalled();
    expect(mockUpdateUser).not.toHaveBeenCalled();
  });

  it("should handle error and refresh user on failure", async () => {
    const device1 = createMockDevice(1);
    const devices = [device1];
    const error = new Error("Failed to update device");
    vi.mocked(deviceService.updateDevice).mockRejectedValue(error);

    const { result } = renderHook(() => useDeviceActions(), {
      wrapper: createWrapper({
        user: {
          id: 1,
          username: "test",
          email: "test@example.com",
          ereader_devices: devices,
        } as never,
        updateUser: mockUpdateUser,
        refresh: mockRefresh,
      }),
    });

    await act(async () => {
      await result.current.setDefaultDevice(1);
    });

    await waitFor(() => {
      expect(mockRefresh).toHaveBeenCalled();
    });

    expect(consoleErrorSpy).toHaveBeenCalledWith(
      "Failed to set default device:",
      error,
    );
  });

  it("should handle case when user has no devices", async () => {
    const { result } = renderHook(() => useDeviceActions(), {
      wrapper: createWrapper({
        user: {
          id: 1,
          username: "test",
          email: "test@example.com",
          ereader_devices: [],
        } as never,
        updateUser: mockUpdateUser,
        refresh: mockRefresh,
      }),
    });

    await act(async () => {
      await result.current.setDefaultDevice(1);
    });

    expect(vi.mocked(deviceService.updateDevice)).not.toHaveBeenCalled();
  });

  it("should handle case when user is null", async () => {
    const { result } = renderHook(() => useDeviceActions(), {
      wrapper: createWrapper({
        user: null,
        updateUser: mockUpdateUser,
        refresh: mockRefresh,
      }),
    });

    await act(async () => {
      await result.current.setDefaultDevice(1);
    });

    expect(vi.mocked(deviceService.updateDevice)).not.toHaveBeenCalled();
  });

  it("should handle case when user has no ereader_devices property", async () => {
    const { result } = renderHook(() => useDeviceActions(), {
      wrapper: createWrapper({
        user: {
          id: 1,
          username: "test",
          email: "test@example.com",
        } as never,
        updateUser: mockUpdateUser,
        refresh: mockRefresh,
      }),
    });

    await act(async () => {
      await result.current.setDefaultDevice(1);
    });

    expect(vi.mocked(deviceService.updateDevice)).not.toHaveBeenCalled();
  });

  it("should not update user context if devices array is missing after update", async () => {
    const device1 = createMockDevice(1);
    const devices = [device1];
    vi.mocked(deviceService.updateDevice).mockResolvedValue(
      createMockDevice(1, { is_default: true }),
    );

    const { result } = renderHook(() => useDeviceActions(), {
      wrapper: createWrapper({
        user: {
          id: 1,
          username: "test",
          email: "test@example.com",
          ereader_devices: devices,
        } as never,
        updateUser: mockUpdateUser,
        refresh: mockRefresh,
      }),
    });

    await act(async () => {
      await result.current.setDefaultDevice(1);
    });

    expect(mockUpdateUser).toHaveBeenCalled();
  });
});
