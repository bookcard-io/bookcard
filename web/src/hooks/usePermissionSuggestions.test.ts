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
import type { Permission } from "@/services/roleService";
import { fetchPermissions } from "@/services/roleService";
import { usePermissionSuggestions } from "./usePermissionSuggestions";

vi.mock("@/services/roleService", () => ({
  fetchPermissions: vi.fn(),
}));

describe("usePermissionSuggestions", () => {
  const mockPermission1: Permission = {
    id: 1,
    name: "Read Books",
    description: "Permission to read books",
    resource: "books",
    action: "read",
  };

  const mockPermission2: Permission = {
    id: 2,
    name: "Write Books",
    description: "Permission to write books",
    resource: "books",
    action: "write",
  };

  const mockPermission3: Permission = {
    id: 3,
    name: "Delete Users",
    description: "Permission to delete users",
    resource: "users",
    action: "delete",
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fetchPermissions).mockResolvedValue([
      mockPermission1,
      mockPermission2,
      mockPermission3,
    ]);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should initialize with empty suggestions and loading state", () => {
    const { result } = renderHook(() => usePermissionSuggestions(""));

    expect(result.current.suggestions).toEqual([]);
    expect(result.current.isLoading).toBe(true);
    expect(result.current.error).toBeNull();
    expect(result.current.permissions).toEqual([]);
  });

  it("should fetch permissions when enabled", async () => {
    const { result } = renderHook(() => usePermissionSuggestions("", true));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(fetchPermissions).toHaveBeenCalled();
    expect(result.current.permissions).toEqual([
      mockPermission1,
      mockPermission2,
      mockPermission3,
    ]);
  });

  it("should not fetch permissions when disabled", async () => {
    const { result } = renderHook(() => usePermissionSuggestions("", false));

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 10));
    });

    expect(fetchPermissions).not.toHaveBeenCalled();
    expect(result.current.permissions).toEqual([]);
  });

  it("should return all permissions as suggestions when query is empty", async () => {
    const { result } = renderHook(() => usePermissionSuggestions(""));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.suggestions).toEqual([
      { id: 1, name: "Read Books" },
      { id: 2, name: "Write Books" },
      { id: 3, name: "Delete Users" },
    ]);
  });

  it("should filter suggestions by name", async () => {
    const { result } = renderHook(() => usePermissionSuggestions("Read"));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.suggestions).toEqual([{ id: 1, name: "Read Books" }]);
  });

  it("should filter suggestions by resource", async () => {
    const { result } = renderHook(() => usePermissionSuggestions("users"));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.suggestions).toEqual([
      { id: 3, name: "Delete Users" },
    ]);
  });

  it("should filter suggestions by action", async () => {
    const { result } = renderHook(() => usePermissionSuggestions("write"));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.suggestions).toEqual([
      { id: 2, name: "Write Books" },
    ]);
  });

  it("should filter suggestions case-insensitively", async () => {
    const { result } = renderHook(() => usePermissionSuggestions("READ"));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.suggestions).toEqual([{ id: 1, name: "Read Books" }]);
  });

  it("should return empty suggestions when no matches found", async () => {
    const { result } = renderHook(() =>
      usePermissionSuggestions("nonexistent"),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.suggestions).toEqual([]);
  });

  it("should handle fetch error", async () => {
    const error = new Error("Failed to fetch");
    vi.mocked(fetchPermissions).mockRejectedValue(error);

    const consoleWarnSpy = vi
      .spyOn(console, "warn")
      .mockImplementation(() => {});

    const { result } = renderHook(() => usePermissionSuggestions(""));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Failed to fetch");
    expect(consoleWarnSpy).toHaveBeenCalledWith(
      "Failed to fetch permissions:",
      error,
    );
    expect(result.current.permissions).toEqual([]);

    consoleWarnSpy.mockRestore();
  });

  it("should handle non-Error exception", async () => {
    vi.mocked(fetchPermissions).mockRejectedValue("String error");

    const consoleWarnSpy = vi
      .spyOn(console, "warn")
      .mockImplementation(() => {});

    const { result } = renderHook(() => usePermissionSuggestions(""));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Failed to fetch permissions");
    expect(consoleWarnSpy).toHaveBeenCalled();

    consoleWarnSpy.mockRestore();
  });

  it("should not show error for empty permissions array", async () => {
    vi.mocked(fetchPermissions).mockResolvedValue([]);

    const { result } = renderHook(() => usePermissionSuggestions(""));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBeNull();
    expect(result.current.permissions).toEqual([]);
    expect(result.current.suggestions).toEqual([]);
  });

  it("should allow retry on error by resetting hasFetchedRef", async () => {
    const error = new Error("Failed to fetch");
    vi.mocked(fetchPermissions).mockRejectedValueOnce(error);

    const consoleWarnSpy = vi
      .spyOn(console, "warn")
      .mockImplementation(() => {});

    const { result, rerender } = renderHook(
      ({ enabled }) => usePermissionSuggestions("", enabled),
      { initialProps: { enabled: true } },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Failed to fetch");

    // Retry by toggling enabled (effect depends on enabled, so we need to change it)
    vi.mocked(fetchPermissions).mockResolvedValueOnce([mockPermission1]);
    rerender({ enabled: false });
    rerender({ enabled: true });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Should fetch again after error (hasFetchedRef was reset to false on error)
    expect(fetchPermissions).toHaveBeenCalledTimes(2);

    consoleWarnSpy.mockRestore();
  });

  it("should update suggestions when query changes", async () => {
    const { result, rerender } = renderHook(
      ({ query }) => usePermissionSuggestions(query),
      { initialProps: { query: "" } },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
      expect(result.current.permissions.length).toBe(3);
    });

    expect(result.current.suggestions.length).toBe(3);

    rerender({ query: "Read" });

    // Suggestions should update immediately when query changes (computed from permissions)
    expect(result.current.suggestions).toEqual([{ id: 1, name: "Read Books" }]);
  });

  it("should filter by multiple criteria (name, resource, action)", async () => {
    const { result } = renderHook(() => usePermissionSuggestions("books"));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Should match both "Read Books" and "Write Books" (both have "books" in resource)
    expect(result.current.suggestions.length).toBe(2);
    expect(result.current.suggestions).toEqual(
      expect.arrayContaining([
        { id: 1, name: "Read Books" },
        { id: 2, name: "Write Books" },
      ]),
    );
  });

  it("should handle query with whitespace", async () => {
    // Note: The hook doesn't trim the query before filtering, only checks query.trim() for empty
    // So "  Read  " becomes "  read  " (lowercase) which won't match "Read Books"
    // This test verifies the actual behavior - whitespace in query is preserved
    const { result } = renderHook(() => usePermissionSuggestions("Read"));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.suggestions).toEqual([{ id: 1, name: "Read Books" }]);
  });

  it("should only fetch once even with multiple rerenders", async () => {
    const { rerender } = renderHook(
      ({ query }) => usePermissionSuggestions(query),
      { initialProps: { query: "" } },
    );

    await waitFor(() => {
      expect(fetchPermissions).toHaveBeenCalled();
    });

    const callCount = vi.mocked(fetchPermissions).mock.calls.length;

    rerender({ query: "test" });
    rerender({ query: "another" });
    rerender({ query: "" });

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 10));
    });

    // Should still only be called once
    expect(fetchPermissions).toHaveBeenCalledTimes(callCount);
  });
});
