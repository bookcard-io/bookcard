import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { EReaderDevice } from "@/components/profile/hooks/useUserProfile";
import {
  createDevice,
  type DeviceCreate,
  type DeviceUpdate,
  deleteDevice,
  updateDevice,
} from "./deviceService";

describe("deviceService", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const createMockDevice = (id: number): EReaderDevice => ({
    id,
    user_id: 1,
    email: "test@example.com",
    device_name: "Test Device",
    device_type: "kindle",
    is_default: false,
    preferred_format: "epub",
  });

  describe("createDevice", () => {
    it("should create device successfully", async () => {
      const deviceData: DeviceCreate = {
        email: "test@example.com",
        device_name: "Test Device",
        device_type: "kindle",
        preferred_format: "epub",
        is_default: false,
      };
      const mockDevice = createMockDevice(1);

      const mockFetchResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue(mockDevice),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      const result = await createDevice(deviceData);

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/devices", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(deviceData),
      });
      expect(result).toEqual(mockDevice);
    });

    it("should throw error when response is not ok with detail", async () => {
      const deviceData: DeviceCreate = {
        email: "test@example.com",
      };
      const errorResponse = { detail: "Email already exists" };

      const mockFetchResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue(errorResponse),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      await expect(createDevice(deviceData)).rejects.toThrow(
        "Email already exists",
      );

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/devices", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(deviceData),
      });
    });

    it("should throw error when response is not ok without detail", async () => {
      const deviceData: DeviceCreate = {
        email: "test@example.com",
      };
      const errorResponse = {};

      const mockFetchResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue(errorResponse),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      await expect(createDevice(deviceData)).rejects.toThrow(
        "Failed to create device",
      );
    });

    it("should throw error when JSON parsing fails", async () => {
      const deviceData: DeviceCreate = {
        email: "test@example.com",
      };

      const mockFetchResponse = {
        ok: false,
        json: vi.fn().mockRejectedValue(new Error("Invalid JSON")),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      await expect(createDevice(deviceData)).rejects.toThrow(
        "Failed to create device",
      );
    });
  });

  describe("updateDevice", () => {
    it("should update device successfully", async () => {
      const deviceId = 1;
      const deviceData: DeviceUpdate = {
        email: "updated@example.com",
        device_name: "Updated Device",
        device_type: "kobo",
        preferred_format: "pdf",
        is_default: true,
      };
      const mockDevice = { ...createMockDevice(deviceId), ...deviceData };

      const mockFetchResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue(mockDevice),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      const result = await updateDevice(deviceId, deviceData);

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/devices/1", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(deviceData),
      });
      expect(result).toEqual(mockDevice);
    });

    it("should throw error when response is not ok with detail", async () => {
      const deviceId = 1;
      const deviceData: DeviceUpdate = {
        email: "test@example.com",
      };
      const errorResponse = { detail: "Device not found" };

      const mockFetchResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue(errorResponse),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      await expect(updateDevice(deviceId, deviceData)).rejects.toThrow(
        "Device not found",
      );

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/devices/1", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(deviceData),
      });
    });

    it("should throw error when response is not ok without detail", async () => {
      const deviceId = 1;
      const deviceData: DeviceUpdate = {
        email: "test@example.com",
      };
      const errorResponse = {};

      const mockFetchResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue(errorResponse),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      await expect(updateDevice(deviceId, deviceData)).rejects.toThrow(
        "Failed to update device",
      );
    });

    it("should throw error when JSON parsing fails", async () => {
      const deviceId = 1;
      const deviceData: DeviceUpdate = {
        email: "test@example.com",
      };

      const mockFetchResponse = {
        ok: false,
        json: vi.fn().mockRejectedValue(new Error("Invalid JSON")),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      await expect(updateDevice(deviceId, deviceData)).rejects.toThrow(
        "Failed to update device",
      );
    });
  });

  describe("deleteDevice", () => {
    it("should delete device successfully", async () => {
      const deviceId = 1;

      const mockFetchResponse = {
        ok: true,
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      await deleteDevice(deviceId);

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/devices/1", {
        method: "DELETE",
        credentials: "include",
      });
    });

    it("should throw error when response is not ok with detail", async () => {
      const deviceId = 1;
      const errorResponse = { detail: "Device not found" };

      const mockFetchResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue(errorResponse),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      await expect(deleteDevice(deviceId)).rejects.toThrow("Device not found");

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/devices/1", {
        method: "DELETE",
        credentials: "include",
      });
    });

    it("should throw error when response is not ok without detail", async () => {
      const deviceId = 1;
      const errorResponse = {};

      const mockFetchResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue(errorResponse),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      await expect(deleteDevice(deviceId)).rejects.toThrow(
        "Failed to delete device",
      );
    });

    it("should throw error when JSON parsing fails", async () => {
      const deviceId = 1;

      const mockFetchResponse = {
        ok: false,
        json: vi.fn().mockRejectedValue(new Error("Invalid JSON")),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      await expect(deleteDevice(deviceId)).rejects.toThrow(
        "Failed to delete device",
      );
    });
  });
});
