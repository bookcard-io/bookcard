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
import type { User } from "@/components/admin/UsersTable";
import {
  createUser,
  deleteUser,
  type UserCreate,
  type UserUpdate,
  updateUser,
} from "./userService";

/**
 * Creates a mock fetch response.
 *
 * Parameters
 * ----------
 * ok : boolean
 *     Response ok status.
 * jsonData : unknown
 *     JSON data to return.
 * jsonError : Error | null
 *     Optional error to throw from json().
 *
 * Returns
 * -------
 * Response
 *     Mock response object.
 */
function createMockResponse(
  ok: boolean,
  jsonData: unknown = {},
  jsonError: Error | null = null,
) {
  return {
    ok,
    json: jsonError
      ? vi.fn().mockRejectedValue(jsonError)
      : vi.fn().mockResolvedValue(jsonData),
  };
}

/**
 * Creates a mock user.
 *
 * Parameters
 * ----------
 * id : number
 *     User ID.
 * overrides : Partial<User>
 *     Optional overrides for default values.
 *
 * Returns
 * -------
 * User
 *     Mock user object.
 */
function createMockUser(id: number, overrides: Partial<User> = {}): User {
  return {
    id,
    username: `user${id}`,
    email: `user${id}@example.com`,
    profile_picture: null,
    is_admin: false,
    default_ereader_email: null,
    roles: [],
    ...overrides,
  };
}

describe("userService", () => {
  const apiBase = "/api/admin/users";
  const baseHeaders = {
    "Content-Type": "application/json",
  };

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("createUser", () => {
    it("should create user successfully", async () => {
      const userData: UserCreate = {
        username: "testuser",
        email: "test@example.com",
        password: "password123",
      };
      const mockUser = createMockUser(1, userData);
      const mockResponse = createMockResponse(true, mockUser);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await createUser(userData);

      expect(globalThis.fetch).toHaveBeenCalledWith(apiBase, {
        method: "POST",
        headers: baseHeaders,
        credentials: "include",
        body: JSON.stringify(userData),
      });
      expect(result).toEqual(mockUser);
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Username already exists" },
        "Username already exists",
      ],
      ["without detail in error response", {}, "Failed to create user"],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to create user",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const userData: UserCreate = {
        username: "testuser",
        email: "test@example.com",
        password: "password123",
      };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(createUser(userData)).rejects.toThrow(expectedMessage);
    });

    it("should throw error when JSON parsing fails", async () => {
      const userData: UserCreate = {
        username: "testuser",
        email: "test@example.com",
        password: "password123",
      };
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(createUser(userData)).rejects.toThrow(
        "Failed to create user",
      );
    });
  });

  describe("updateUser", () => {
    const userId = 1;
    const url = `${apiBase}/${userId}`;

    it("should update user successfully", async () => {
      const userData: UserUpdate = {
        email: "updated@example.com",
        is_active: false,
      };
      const mockUser = createMockUser(userId, userData);
      const mockResponse = createMockResponse(true, mockUser);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await updateUser(userId, userData);

      expect(globalThis.fetch).toHaveBeenCalledWith(url, {
        method: "PUT",
        headers: baseHeaders,
        credentials: "include",
        body: JSON.stringify(userData),
      });
      expect(result).toEqual(mockUser);
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "User not found" },
        "User not found",
      ],
      ["without detail in error response", {}, "Failed to update user"],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to update user",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const userData: UserUpdate = { email: "updated@example.com" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(updateUser(userId, userData)).rejects.toThrow(
        expectedMessage,
      );
    });

    it("should throw error when JSON parsing fails", async () => {
      const userData: UserUpdate = { email: "updated@example.com" };
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(updateUser(userId, userData)).rejects.toThrow(
        "Failed to update user",
      );
    });
  });

  describe("deleteUser", () => {
    const userId = 1;
    const url = `${apiBase}/${userId}`;

    it("should delete user successfully", async () => {
      const mockResponse = createMockResponse(true);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await deleteUser(userId);

      expect(globalThis.fetch).toHaveBeenCalledWith(url, {
        method: "DELETE",
        credentials: "include",
      });
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "User not found" },
        "User not found",
      ],
      ["without detail in error response", {}, "Failed to delete user"],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to delete user",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(deleteUser(userId)).rejects.toThrow(expectedMessage);
    });

    it("should throw error when JSON parsing fails", async () => {
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(deleteUser(userId)).rejects.toThrow("Failed to delete user");
    });
  });
});
