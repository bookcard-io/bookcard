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

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fetchSettings, type Setting, saveSetting } from "./settingsApi";

/**
 * Creates a mock fetch response.
 *
 * Parameters
 * ----------
 * ok : boolean
 *     Response ok status.
 * jsonData : unknown
 *     JSON data to return.
 *
 * Returns
 * -------
 * Response
 *     Mock response object.
 */
function createMockResponse(ok: boolean, jsonData: unknown = {}) {
  return {
    ok,
    json: vi.fn().mockResolvedValue(jsonData),
  };
}

/**
 * Creates a mock setting.
 *
 * Parameters
 * ----------
 * key : string
 *     Setting key.
 * value : string
 *     Setting value.
 * overrides : Partial<Setting>
 *     Optional overrides for default values.
 *
 * Returns
 * -------
 * Setting
 *     Mock setting object.
 */
function createMockSetting(
  key: string,
  value: string,
  overrides: Partial<Setting> = {},
): Setting {
  return {
    key,
    value,
    description: `Description for ${key}`,
    updated_at: "2025-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("settingsApi", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("fetchSettings", () => {
    it("should fetch settings successfully", async () => {
      const mockSettings = {
        settings: {
          theme: createMockSetting("theme", "dark"),
          language: createMockSetting("language", "en"),
        },
      };
      const mockResponse = createMockResponse(true, mockSettings);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await fetchSettings();

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/auth/settings", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      });
      expect(result).toEqual(mockSettings);
    });

    it("should throw error when response is not ok", async () => {
      const mockResponse = createMockResponse(false);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(fetchSettings()).rejects.toThrow("Failed to fetch settings");
    });
  });

  describe("saveSetting", () => {
    const key = "theme";
    const value = "light";
    const encodedKey = encodeURIComponent(key);
    const url = `/api/auth/settings/${encodedKey}`;
    const baseHeaders = {
      "Content-Type": "application/json",
    };

    it("should save setting successfully", async () => {
      const mockSetting = createMockSetting(key, value);
      const mockResponse = createMockResponse(true, mockSetting);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await saveSetting(key, value);

      expect(globalThis.fetch).toHaveBeenCalledWith(url, {
        method: "PUT",
        headers: baseHeaders,
        body: JSON.stringify({ value }),
        credentials: "include",
      });
      expect(result).toEqual(mockSetting);
    });

    it("should encode special characters in key", async () => {
      const specialKey = "theme/preference";
      const encodedSpecialKey = encodeURIComponent(specialKey);
      const mockSetting = createMockSetting(specialKey, value);
      const mockResponse = createMockResponse(true, mockSetting);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await saveSetting(specialKey, value);

      expect(globalThis.fetch).toHaveBeenCalledWith(
        `/api/auth/settings/${encodedSpecialKey}`,
        expect.any(Object),
      );
    });

    it.each<[string, { detail?: string }, string]>([
      [
        "with detail in error response",
        { detail: "Validation error" },
        "Validation error",
      ],
      ["without detail in error response", {}, `Failed to save setting ${key}`],
      [
        "with empty detail in error response",
        { detail: "" },
        `Failed to save setting ${key}`,
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(saveSetting(key, value)).rejects.toThrow(expectedMessage);
    });
  });
});
