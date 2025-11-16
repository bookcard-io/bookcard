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
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Permission } from "@/services/roleService";
import { fetchPermissions } from "@/services/roleService";
import { useRolePermissions } from "./useRolePermissions";

vi.mock("@/services/roleService", () => ({
  fetchPermissions: vi.fn(),
}));

describe("useRolePermissions", () => {
  const mockPermission1: Permission = {
    id: 1,
    name: "permission-1",
    description: "Permission 1",
    resource: "resource-1",
    action: "action-1",
  };

  const mockPermission2: Permission = {
    id: 2,
    name: "permission-2",
    description: "Permission 2",
    resource: "resource-2",
    action: "action-2",
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should initialize with empty permission names when no initial names provided", () => {
    const { result } = renderHook(() => useRolePermissions());

    expect(result.current.permissionNames).toEqual([]);
    expect(result.current.existingPermissionNames).toEqual([]);
    expect(result.current.newPermissionNames).toEqual([]);
  });

  it("should initialize with provided initial permission names", () => {
    const { result } = renderHook(() =>
      useRolePermissions({
        initialPermissionNames: ["permission-1", "permission-2"],
        availablePermissions: [mockPermission1, mockPermission2],
      }),
    );

    expect(result.current.permissionNames).toEqual([
      "permission-1",
      "permission-2",
    ]);
    expect(result.current.existingPermissionNames).toEqual([
      "permission-1",
      "permission-2",
    ]);
    expect(result.current.newPermissionNames).toEqual([]);
  });

  it("should separate existing and new permission names", () => {
    const { result } = renderHook(() =>
      useRolePermissions({
        initialPermissionNames: ["permission-1", "new-permission"],
        availablePermissions: [mockPermission1],
      }),
    );

    expect(result.current.existingPermissionNames).toEqual(["permission-1"]);
    expect(result.current.newPermissionNames).toEqual(["new-permission"]);
  });

  it("should create permission map from available permissions", () => {
    const { result } = renderHook(() =>
      useRolePermissions({
        availablePermissions: [mockPermission1, mockPermission2],
      }),
    );

    expect(result.current.permissionMap.has("permission-1")).toBe(true);
    expect(result.current.permissionMap.has("permission-2")).toBe(true);
    expect(result.current.permissionMap.get("permission-1")).toEqual(
      mockPermission1,
    );
  });

  it("should fetch permissions when not provided", async () => {
    vi.mocked(fetchPermissions).mockResolvedValue([
      mockPermission1,
      mockPermission2,
    ]);

    const { result } = renderHook(() => useRolePermissions());

    expect(result.current.isLoadingPermissions).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoadingPermissions).toBe(false);
    });

    expect(fetchPermissions).toHaveBeenCalled();
    expect(result.current.allPermissions).toEqual([
      mockPermission1,
      mockPermission2,
    ]);
  });

  it("should not fetch permissions when available permissions are provided", () => {
    const { result } = renderHook(() =>
      useRolePermissions({
        availablePermissions: [mockPermission1],
      }),
    );

    expect(fetchPermissions).not.toHaveBeenCalled();
    expect(result.current.allPermissions).toEqual([mockPermission1]);
  });

  it("should handle fetch permissions error gracefully", async () => {
    const consoleErrorSpy = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});
    vi.mocked(fetchPermissions).mockRejectedValue(new Error("Fetch failed"));

    const { result } = renderHook(() => useRolePermissions());

    await waitFor(() => {
      expect(result.current.isLoadingPermissions).toBe(false);
    });

    expect(consoleErrorSpy).toHaveBeenCalled();
    expect(result.current.allPermissions).toEqual([]);

    consoleErrorSpy.mockRestore();
  });

  it("should update permission names", () => {
    const { result } = renderHook(() => useRolePermissions());

    act(() => {
      result.current.setPermissionNames(["permission-1", "permission-2"]);
    });

    expect(result.current.permissionNames).toEqual([
      "permission-1",
      "permission-2",
    ]);
  });

  it("should remove existing permission", () => {
    const { result } = renderHook(() =>
      useRolePermissions({
        initialPermissionNames: ["permission-1", "permission-2"],
        availablePermissions: [mockPermission1, mockPermission2],
      }),
    );

    act(() => {
      result.current.removeExistingPermission("permission-1");
    });

    expect(result.current.permissionNames).toEqual(["permission-2"]);
  });

  it("should remove new permission and clean up details", () => {
    const { result } = renderHook(() =>
      useRolePermissions({
        initialPermissionNames: ["new-permission"],
      }),
    );

    act(() => {
      result.current.updateNewPermissionDetail(
        "new-permission",
        "description",
        "Test description",
      );
    });

    expect(result.current.newPermissionDetails["new-permission"]).toBeDefined();

    act(() => {
      result.current.removeNewPermission("new-permission");
    });

    expect(result.current.permissionNames).toEqual([]);
    expect(
      result.current.newPermissionDetails["new-permission"],
    ).toBeUndefined();
    expect(result.current.conditionErrors["new-permission"]).toBeUndefined();
  });

  it("should update new permission detail", () => {
    const { result } = renderHook(() =>
      useRolePermissions({
        initialPermissionNames: ["new-permission"],
      }),
    );

    act(() => {
      result.current.updateNewPermissionDetail(
        "new-permission",
        "description",
        "Test description",
      );
    });

    expect(result.current.newPermissionDetails["new-permission"]).toEqual({
      description: "Test description",
      resource: "",
      action: "",
      condition: "",
    });
  });

  it("should initialize new permission detail with empty values", () => {
    const { result } = renderHook(() => useRolePermissions());

    act(() => {
      result.current.updateNewPermissionDetail(
        "new-permission",
        "resource",
        "test-resource",
      );
    });

    expect(result.current.newPermissionDetails["new-permission"]).toEqual({
      description: "",
      resource: "test-resource",
      action: "",
      condition: "",
    });
  });

  it("should validate condition JSON when updating condition field", () => {
    const { result } = renderHook(() =>
      useRolePermissions({
        initialPermissionNames: ["new-permission"],
      }),
    );

    act(() => {
      result.current.updateNewPermissionDetail(
        "new-permission",
        "condition",
        '{"key": "value"}',
      );
    });

    expect(result.current.conditionErrors["new-permission"]).toBe("");
  });

  it("should set condition error for invalid JSON", () => {
    const { result } = renderHook(() =>
      useRolePermissions({
        initialPermissionNames: ["new-permission"],
      }),
    );

    act(() => {
      result.current.updateNewPermissionDetail(
        "new-permission",
        "condition",
        "{invalid json}",
      );
    });

    expect(result.current.conditionErrors["new-permission"]).toBeDefined();
    expect(result.current.conditionErrors["new-permission"]).toContain(
      "Invalid JSON",
    );
  });

  it("should clear condition error for empty condition", () => {
    const { result } = renderHook(() =>
      useRolePermissions({
        initialPermissionNames: ["new-permission"],
      }),
    );

    act(() => {
      result.current.updateNewPermissionDetail(
        "new-permission",
        "condition",
        "{invalid}",
      );
    });

    expect(result.current.conditionErrors["new-permission"]).toBeDefined();

    act(() => {
      result.current.updateNewPermissionDetail(
        "new-permission",
        "condition",
        "",
      );
    });

    expect(result.current.conditionErrors["new-permission"]).toBe("");
  });

  it("should not validate condition for non-condition fields", () => {
    const { result } = renderHook(() =>
      useRolePermissions({
        initialPermissionNames: ["new-permission"],
      }),
    );

    act(() => {
      result.current.updateNewPermissionDetail(
        "new-permission",
        "description",
        "Test description",
      );
    });

    expect(result.current.conditionErrors["new-permission"]).toBeUndefined();
  });

  it("should reset to initial state", () => {
    const { result } = renderHook(() =>
      useRolePermissions({
        initialPermissionNames: ["permission-1"],
        availablePermissions: [mockPermission1],
      }),
    );

    act(() => {
      result.current.setPermissionNames(["permission-2"]);
      result.current.updateNewPermissionDetail(
        "new-permission",
        "description",
        "Test",
      );
    });

    act(() => {
      result.current.reset();
    });

    expect(result.current.permissionNames).toEqual(["permission-1"]);
    expect(result.current.newPermissionDetails).toEqual({});
    expect(result.current.conditionErrors).toEqual({});
  });

  it("should update existing permission detail when updating field", () => {
    const { result } = renderHook(() =>
      useRolePermissions({
        initialPermissionNames: ["new-permission"],
      }),
    );

    act(() => {
      result.current.updateNewPermissionDetail(
        "new-permission",
        "description",
        "First description",
      );
    });

    act(() => {
      result.current.updateNewPermissionDetail(
        "new-permission",
        "resource",
        "test-resource",
      );
    });

    expect(result.current.newPermissionDetails["new-permission"]).toEqual({
      description: "First description",
      resource: "test-resource",
      action: "",
      condition: "",
    });
  });
});
