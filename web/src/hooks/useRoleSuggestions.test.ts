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

import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Role } from "@/services/roleService";
import { useRoleSuggestions } from "./useRoleSuggestions";

vi.mock("@/services/roleService", () => ({
  fetchRoles: vi.fn(),
}));

import * as roleService from "@/services/roleService";

/**
 * Creates a mock role.
 *
 * Parameters
 * ----------
 * id : number
 *     Role ID.
 * name : string
 *     Role name.
 * description : string | null
 *     Optional role description.
 *
 * Returns
 * -------
 * Role
 *     Mock role object.
 */
function createMockRole(
  id: number,
  name: string,
  description: string | null = null,
): Role {
  return { id, name, description, permissions: [] };
}

describe("useRoleSuggestions", () => {
  const consoleErrorSpy = vi
    .spyOn(console, "error")
    .mockImplementation(() => {});

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    consoleErrorSpy.mockClear();
  });

  it("should initialize with empty state", () => {
    vi.mocked(roleService.fetchRoles).mockResolvedValue([]);

    const { result } = renderHook(() => useRoleSuggestions("", false));

    expect(result.current.suggestions).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.roles).toEqual([]);
  });

  it("should fetch roles when enabled", async () => {
    const mockRoles = [createMockRole(1, "Admin"), createMockRole(2, "User")];
    vi.mocked(roleService.fetchRoles).mockResolvedValue(mockRoles);

    const { result } = renderHook(() => useRoleSuggestions("", true));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.roles).toEqual(mockRoles);
    expect(vi.mocked(roleService.fetchRoles)).toHaveBeenCalledTimes(1);
  });

  it("should not fetch roles when enabled is false", () => {
    renderHook(() => useRoleSuggestions("", false));

    expect(vi.mocked(roleService.fetchRoles)).not.toHaveBeenCalled();
  });

  it("should not fetch roles multiple times", async () => {
    const mockRoles = [createMockRole(1, "Admin")];
    vi.mocked(roleService.fetchRoles).mockResolvedValue(mockRoles);

    const { rerender } = renderHook(() => useRoleSuggestions("", true));

    await waitFor(() => {
      expect(vi.mocked(roleService.fetchRoles)).toHaveBeenCalledTimes(1);
    });

    rerender({ query: "test", enabled: true });

    await waitFor(() => {
      // Should still only be called once
      expect(vi.mocked(roleService.fetchRoles)).toHaveBeenCalledTimes(1);
    });
  });

  it("should return all roles when query is empty", async () => {
    const mockRoles = [createMockRole(1, "Admin"), createMockRole(2, "User")];
    vi.mocked(roleService.fetchRoles).mockResolvedValue(mockRoles);

    const { result } = renderHook(() => useRoleSuggestions("", true));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.suggestions).toHaveLength(2);
    expect(result.current.suggestions[0]).toEqual({ id: 1, name: "Admin" });
    expect(result.current.suggestions[1]).toEqual({ id: 2, name: "User" });
  });

  it("should return all roles when query is whitespace only", async () => {
    const mockRoles = [createMockRole(1, "Admin"), createMockRole(2, "User")];
    vi.mocked(roleService.fetchRoles).mockResolvedValue(mockRoles);

    const { result } = renderHook(() => useRoleSuggestions("   ", true));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.suggestions).toHaveLength(2);
  });

  it("should filter roles by query", async () => {
    const mockRoles = [
      createMockRole(1, "Admin"),
      createMockRole(2, "User"),
      createMockRole(3, "Moderator"),
    ];
    vi.mocked(roleService.fetchRoles).mockResolvedValue(mockRoles);

    const { result } = renderHook(() => useRoleSuggestions("admin", true));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.suggestions).toHaveLength(1);
    expect(result.current.suggestions[0]).toEqual({ id: 1, name: "Admin" });
  });

  it("should filter roles case-insensitively", async () => {
    const mockRoles = [createMockRole(1, "Admin"), createMockRole(2, "User")];
    vi.mocked(roleService.fetchRoles).mockResolvedValue(mockRoles);

    const { result } = renderHook(() => useRoleSuggestions("ADMIN", true));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.suggestions).toHaveLength(1);
    expect(result.current.suggestions[0]?.name).toBe("Admin");
  });

  it("should filter roles by partial match", async () => {
    const mockRoles = [
      createMockRole(1, "Administrator"),
      createMockRole(2, "User"),
    ];
    vi.mocked(roleService.fetchRoles).mockResolvedValue(mockRoles);

    const { result } = renderHook(() => useRoleSuggestions("min", true));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.suggestions).toHaveLength(1);
    expect(result.current.suggestions[0]?.name).toBe("Administrator");
  });

  it("should handle fetch error", async () => {
    const error = new Error("Failed to fetch roles");
    vi.mocked(roleService.fetchRoles).mockRejectedValue(error);

    const { result } = renderHook(() => useRoleSuggestions("", true));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Failed to fetch roles");
    expect(result.current.roles).toEqual([]);
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      "Failed to fetch roles:",
      error,
    );
  });

  it("should handle fetch error with non-Error object", async () => {
    vi.mocked(roleService.fetchRoles).mockRejectedValue("String error");

    const { result } = renderHook(() => useRoleSuggestions("", true));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Failed to fetch roles");
  });

  it("should allow retry after error by resetting hasFetchedRef", async () => {
    const error = new Error("Failed to fetch");
    vi.mocked(roleService.fetchRoles)
      .mockRejectedValueOnce(error)
      .mockResolvedValueOnce([createMockRole(1, "Admin")]);

    const { result, unmount } = renderHook(
      ({ enabled }) => useRoleSuggestions("", enabled),
      { initialProps: { enabled: true } },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // When error is an Error object, it uses err.message
    expect(result.current.error).toBe("Failed to fetch");
    // hasFetchedRef should be reset to false on error
    expect(vi.mocked(roleService.fetchRoles)).toHaveBeenCalledTimes(1);

    // Unmount and remount to trigger retry (hasFetchedRef is reset)
    unmount();

    const { result: result2 } = renderHook(
      ({ enabled }) => useRoleSuggestions("", enabled),
      { initialProps: { enabled: true } },
    );

    await waitFor(() => {
      expect(result2.current.isLoading).toBe(false);
    });

    expect(result2.current.error).toBeNull();
    expect(result2.current.roles).toHaveLength(1);
    expect(vi.mocked(roleService.fetchRoles)).toHaveBeenCalledTimes(2);
  });

  it("should update suggestions when query changes", async () => {
    const mockRoles = [createMockRole(1, "Admin"), createMockRole(2, "User")];
    vi.mocked(roleService.fetchRoles).mockResolvedValue(mockRoles);

    const { result, rerender } = renderHook(
      ({ query }) => useRoleSuggestions(query, true),
      { initialProps: { query: "" } },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.suggestions).toHaveLength(2);

    // Change query
    rerender({ query: "admin" });

    // Suggestions should update immediately (no async operation)
    expect(result.current.suggestions).toHaveLength(1);
    expect(result.current.suggestions[0]?.name).toBe("Admin");
  });
});
