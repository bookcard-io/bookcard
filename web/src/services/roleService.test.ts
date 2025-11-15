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
import * as fetchUtils from "@/utils/fetch";
import { fetchRoles, type Role } from "./roleService";

/**
 * Creates a mock role.
 *
 * Parameters
 * ----------
 * id : number
 *     Role ID.
 * overrides : Partial<Role>
 *     Optional overrides for default values.
 *
 * Returns
 * -------
 * Role
 *     Mock role object.
 */
function createMockRole(id: number, overrides: Partial<Role> = {}): Role {
  return {
    id,
    name: `Role ${id}`,
    description: `Description for role ${id}`,
    permissions: [],
    ...overrides,
  };
}

describe("roleService", () => {
  const apiBase = "/api/admin/roles";
  const baseHeaders = {
    "Content-Type": "application/json",
  };

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("fetchRoles", () => {
    it("should fetch roles successfully", async () => {
      const mockRoles = [
        createMockRole(1),
        createMockRole(2, { description: null }),
      ];
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue(mockRoles),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      vi.spyOn(fetchUtils, "deduplicateFetch").mockImplementation(
        async (_url, fetcher) => fetcher(),
      );

      const result = await fetchRoles();

      expect(globalThis.fetch).toHaveBeenCalledWith(apiBase, {
        method: "GET",
        headers: baseHeaders,
        credentials: "include",
      });
      expect(result).toEqual(mockRoles);
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Unauthorized" },
        "Unauthorized",
      ],
      ["without detail in error response", {}, "Failed to fetch roles"],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to fetch roles",
      ],
    ])(
      "should throw error when response is not ok %s",
      async (_desc, errorData, expectedMessage) => {
        const mockResponse = {
          ok: false,
          json: vi.fn().mockResolvedValue(errorData),
        };
        (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
          mockResponse,
        );

        vi.spyOn(fetchUtils, "deduplicateFetch").mockImplementation(
          async (_url, fetcher) => fetcher(),
        );

        await expect(fetchRoles()).rejects.toThrow(expectedMessage);
      },
    );

    it("should throw error when JSON parsing fails", async () => {
      const mockResponse = {
        ok: false,
        json: vi.fn().mockRejectedValue(new Error("Invalid JSON")),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      vi.spyOn(fetchUtils, "deduplicateFetch").mockImplementation(
        async (_url, fetcher) => fetcher(),
      );

      await expect(fetchRoles()).rejects.toThrow("Failed to fetch roles");
    });
  });
});
