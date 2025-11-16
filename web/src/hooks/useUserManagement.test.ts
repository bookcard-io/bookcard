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
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { User } from "@/components/admin/UsersTable";
import { useUserManagement } from "./useUserManagement";

vi.mock("@/services/userService", () => ({
  createUser: vi.fn(),
  updateUser: vi.fn(),
  deleteUser: vi.fn(),
}));

import { createUser, deleteUser, updateUser } from "@/services/userService";

describe("useUserManagement", () => {
  let mockFetch: ReturnType<typeof vi.fn>;

  const mockUser1: User = {
    id: 1,
    username: "user1",
    email: "user1@example.com",
    profile_picture: null,
    is_admin: false,
    default_ereader_email: null,
    roles: [],
  };

  const mockUser2: User = {
    id: 2,
    username: "user2",
    email: "user2@example.com",
    profile_picture: null,
    is_admin: false,
    default_ereader_email: null,
    roles: [],
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch = vi.fn();
    vi.stubGlobal("fetch", mockFetch);

    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => [mockUser1, mockUser2],
    } as Response);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("should initialize with loading state and fetch users", async () => {
    const { result } = renderHook(() => useUserManagement());

    expect(result.current.isLoading).toBe(true);
    expect(result.current.users).toEqual([]);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/admin/users?limit=100&offset=0",
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      },
    );
    expect(result.current.users).toEqual([mockUser1, mockUser2]);
  });

  it("should handle fetch error gracefully", async () => {
    const error = new Error("Failed to fetch");
    mockFetch.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useUserManagement());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.users).toEqual([]);
  });

  it("should create a new user", async () => {
    const newUser: User = {
      id: 3,
      username: "user3",
      email: "user3@example.com",
      profile_picture: null,
      is_admin: false,
      default_ereader_email: null,
      roles: [],
    };

    vi.mocked(createUser).mockResolvedValue(newUser);

    const { result } = renderHook(() => useUserManagement());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    let createdUser: User | undefined;
    await act(async () => {
      createdUser = await result.current.handleCreate({
        username: "user3",
        email: "user3@example.com",
        password: "password123",
      });
    });

    expect(createUser).toHaveBeenCalledWith({
      username: "user3",
      email: "user3@example.com",
      password: "password123",
    });
    expect(result.current.users).toContainEqual(newUser);
    expect(createdUser).toEqual(newUser);
  });

  it("should update an existing user", async () => {
    const updatedUser: User = {
      ...mockUser1,
      username: "updated_user1",
      email: "updated@example.com",
    };

    vi.mocked(updateUser).mockResolvedValue(updatedUser);

    const { result } = renderHook(() => useUserManagement());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    let savedUser: User | undefined;
    await act(async () => {
      savedUser = await result.current.handleUpdate(1, {
        username: "updated_user1",
        email: "updated@example.com",
      });
    });

    expect(updateUser).toHaveBeenCalledWith(1, {
      username: "updated_user1",
      email: "updated@example.com",
    });
    expect(result.current.users.find((u) => u.id === 1)).toEqual(updatedUser);
    expect(savedUser).toEqual(updatedUser);
  });

  it("should delete a user", async () => {
    vi.mocked(deleteUser).mockResolvedValue(undefined);

    const { result } = renderHook(() => useUserManagement());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.users.length).toBe(2);

    await act(async () => {
      await result.current.handleDelete(1);
    });

    expect(deleteUser).toHaveBeenCalledWith(1);
    expect(result.current.users.length).toBe(1);
    expect(result.current.users.find((u) => u.id === 1)).toBeUndefined();
    expect(result.current.users).toContainEqual(mockUser2);
  });

  it("should refresh users list", async () => {
    const { result } = renderHook(() => useUserManagement());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const initialCallCount = mockFetch.mock.calls.length;

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [mockUser1],
    } as Response);

    await act(async () => {
      await result.current.refresh();
    });

    expect(mockFetch).toHaveBeenCalledTimes(initialCallCount + 1);
    expect(result.current.users).toEqual([mockUser1]);
  });

  it("should handle create error", async () => {
    const error = new Error("Failed to create user");
    vi.mocked(createUser).mockRejectedValueOnce(error);

    const { result } = renderHook(() => useUserManagement());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      try {
        await result.current.handleCreate({
          username: "user3",
          email: "user3@example.com",
          password: "password123",
        });
      } catch {
        // Expected to throw
      }
    });

    expect(result.current.users).toEqual([mockUser1, mockUser2]);
  });

  it("should handle update error", async () => {
    const error = new Error("Failed to update user");
    vi.mocked(updateUser).mockRejectedValueOnce(error);

    const { result } = renderHook(() => useUserManagement());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      try {
        await result.current.handleUpdate(1, {
          username: "updated_user1",
        });
      } catch {
        // Expected to throw
      }
    });

    // Users should remain unchanged on error
    expect(result.current.users).toEqual([mockUser1, mockUser2]);
  });

  it("should handle delete error", async () => {
    const error = new Error("Failed to delete user");
    vi.mocked(deleteUser).mockRejectedValueOnce(error);

    const { result } = renderHook(() => useUserManagement());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      try {
        await result.current.handleDelete(1);
      } catch {
        // Expected to throw
      }
    });

    // Users should remain unchanged on error
    expect(result.current.users).toEqual([mockUser1, mockUser2]);
  });
});
