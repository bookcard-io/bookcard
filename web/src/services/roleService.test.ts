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
import {
  createPermission,
  createRole,
  deletePermission,
  deleteRole,
  fetchPermissions,
  fetchRoles,
  type Permission,
  type Role,
  type RoleCreate,
  type RoleUpdate,
  updatePermission,
  updateRole,
  updateRolePermission,
} from "./roleService";

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
  const PERMISSIONS_API_BASE = "/api/admin/permissions";
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

  describe("fetchPermissions", () => {
    it("should fetch permissions successfully", async () => {
      const mockPermissions: Permission[] = [
        {
          id: 1,
          name: "Read Books",
          description: "Permission to read books",
          resource: "books",
          action: "read",
        },
      ];
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue(mockPermissions),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      vi.spyOn(fetchUtils, "deduplicateFetch").mockImplementation(
        async (_url, fetcher) => fetcher(),
      );

      const result = await fetchPermissions();

      expect(globalThis.fetch).toHaveBeenCalledWith(PERMISSIONS_API_BASE, {
        method: "GET",
        headers: baseHeaders,
        credentials: "include",
      });
      expect(result).toEqual(mockPermissions);
    });

    it("should return empty array on 404", async () => {
      const consoleWarnSpy = vi
        .spyOn(console, "warn")
        .mockImplementation(() => {});
      const mockResponse = {
        ok: false,
        status: 404,
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      vi.spyOn(fetchUtils, "deduplicateFetch").mockImplementation(
        async (_url, fetcher) => fetcher(),
      );

      const result = await fetchPermissions();

      expect(result).toEqual([]);
      expect(consoleWarnSpy).toHaveBeenCalled();

      consoleWarnSpy.mockRestore();
    });

    it("should return empty array on non-404 error", async () => {
      const consoleWarnSpy = vi
        .spyOn(console, "warn")
        .mockImplementation(() => {});
      const mockResponse = {
        ok: false,
        status: 500,
        json: vi.fn().mockResolvedValue({ detail: "Server error" }),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      vi.spyOn(fetchUtils, "deduplicateFetch").mockImplementation(
        async (_url, fetcher) => fetcher(),
      );

      const result = await fetchPermissions();

      expect(result).toEqual([]);
      expect(consoleWarnSpy).toHaveBeenCalled();

      consoleWarnSpy.mockRestore();
    });

    it("should return empty array when JSON parsing fails", async () => {
      const consoleWarnSpy = vi
        .spyOn(console, "warn")
        .mockImplementation(() => {});
      const mockResponse = {
        ok: false,
        status: 500,
        json: vi.fn().mockRejectedValue(new Error("Invalid JSON")),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      vi.spyOn(fetchUtils, "deduplicateFetch").mockImplementation(
        async (_url, fetcher) => fetcher(),
      );

      const result = await fetchPermissions();

      expect(result).toEqual([]);
      expect(consoleWarnSpy).toHaveBeenCalled();

      consoleWarnSpy.mockRestore();
    });

    it("should return empty array on network error", async () => {
      const consoleWarnSpy = vi
        .spyOn(console, "warn")
        .mockImplementation(() => {});
      const error = new Error("Network error");
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(error);

      vi.spyOn(fetchUtils, "deduplicateFetch").mockImplementation(
        async (_url, fetcher) => fetcher(),
      );

      const result = await fetchPermissions();

      expect(result).toEqual([]);
      expect(consoleWarnSpy).toHaveBeenCalled();

      consoleWarnSpy.mockRestore();
    });
  });

  describe("createRole", () => {
    it("should create role successfully", async () => {
      const roleData: RoleCreate = {
        name: "New Role",
        description: "Test Description",
      };
      const mockRole = createMockRole(1, {
        name: "New Role",
        description: "Test Description",
      });
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue(mockRole),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await createRole(roleData);

      expect(globalThis.fetch).toHaveBeenCalledWith(apiBase, {
        method: "POST",
        headers: baseHeaders,
        credentials: "include",
        body: JSON.stringify(roleData),
      });
      expect(result).toEqual(mockRole);
    });

    it("should throw error when response is not ok", async () => {
      const roleData: RoleCreate = {
        name: "New Role",
      };
      const mockResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue({ detail: "Role already exists" }),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(createRole(roleData)).rejects.toThrow("Role already exists");
    });

    it("should throw default error when detail is missing", async () => {
      const roleData: RoleCreate = {
        name: "New Role",
      };
      const mockResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue({}),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(createRole(roleData)).rejects.toThrow(
        "Failed to create role",
      );
    });

    it("should handle JSON parsing error", async () => {
      const roleData: RoleCreate = {
        name: "New Role",
      };
      const mockResponse = {
        ok: false,
        json: vi.fn().mockRejectedValue(new Error("Invalid JSON")),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(createRole(roleData)).rejects.toThrow(
        "Failed to create role",
      );
    });
  });

  describe("updateRole", () => {
    it("should update role successfully", async () => {
      const roleData: RoleUpdate = {
        name: "Updated Role",
        description: "Updated Description",
      };
      const mockRole = createMockRole(1, {
        name: "Updated Role",
        description: "Updated Description",
      });
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue(mockRole),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await updateRole(1, roleData);

      expect(globalThis.fetch).toHaveBeenCalledWith(`${apiBase}/1`, {
        method: "PUT",
        headers: baseHeaders,
        credentials: "include",
        body: JSON.stringify(roleData),
      });
      expect(result).toEqual(mockRole);
    });

    it("should throw error when response is not ok", async () => {
      const roleData: RoleUpdate = {
        name: "Updated Role",
      };
      const mockResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue({ detail: "Role not found" }),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(updateRole(1, roleData)).rejects.toThrow("Role not found");
    });
  });

  describe("deleteRole", () => {
    it("should delete role successfully", async () => {
      const mockResponse = {
        ok: true,
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await deleteRole(1);

      expect(globalThis.fetch).toHaveBeenCalledWith(`${apiBase}/1`, {
        method: "DELETE",
        credentials: "include",
      });
    });

    it("should throw error for locked role", async () => {
      const mockResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue({
          detail: "cannot_delete_locked_role",
        }),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(deleteRole(1)).rejects.toThrow(
        "Cannot delete locked role. Locked roles cannot be deleted.",
      );
    });

    it("should throw error when role is assigned to users", async () => {
      const mockResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue({
          detail: "role_assigned_to_users",
        }),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(deleteRole(1)).rejects.toThrow(
        "Cannot delete role. This role is assigned to one or more users. Please remove the role from all users before deleting.",
      );
    });

    it("should throw error when role not found", async () => {
      const mockResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue({
          detail: "role_not_found",
        }),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(deleteRole(1)).rejects.toThrow(
        "Role not found. It may have already been deleted.",
      );
    });

    it("should throw default error when detail is missing", async () => {
      const mockResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue({}),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(deleteRole(1)).rejects.toThrow("Failed to delete role");
    });
  });

  describe("createPermission", () => {
    it("should create permission successfully", async () => {
      const permissionData = {
        name: "Read Books",
        description: "Permission to read books",
        resource: "books",
        action: "read",
      };
      const mockPermission: Permission = {
        id: 1,
        ...permissionData,
      };
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue(mockPermission),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await createPermission(permissionData);

      expect(globalThis.fetch).toHaveBeenCalledWith(PERMISSIONS_API_BASE, {
        method: "POST",
        headers: baseHeaders,
        credentials: "include",
        body: JSON.stringify(permissionData),
      });
      expect(result).toEqual(mockPermission);
    });

    it("should throw error when response is not ok", async () => {
      const permissionData = {
        name: "Read Books",
        resource: "books",
        action: "read",
      };
      const mockResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue({ detail: "Permission exists" }),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(createPermission(permissionData)).rejects.toThrow(
        "Permission exists",
      );
    });
  });

  describe("updatePermission", () => {
    it("should update permission successfully", async () => {
      const permissionData = {
        name: "Updated Permission",
        description: "Updated Description",
      };
      const mockPermission: Permission = {
        id: 1,
        name: "Updated Permission",
        description: "Updated Description",
        resource: "books",
        action: "read",
      };
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue(mockPermission),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await updatePermission(1, permissionData);

      expect(globalThis.fetch).toHaveBeenCalledWith(
        `${PERMISSIONS_API_BASE}/1`,
        {
          method: "PUT",
          headers: baseHeaders,
          credentials: "include",
          body: JSON.stringify(permissionData),
        },
      );
      expect(result).toEqual(mockPermission);
    });

    it("should throw error when response is not ok", async () => {
      const permissionData = {
        name: "Updated Permission",
      };
      const mockResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue({ detail: "Permission not found" }),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(updatePermission(1, permissionData)).rejects.toThrow(
        "Permission not found",
      );
    });
  });

  describe("deletePermission", () => {
    it("should delete permission successfully", async () => {
      const mockResponse = {
        ok: true,
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await deletePermission(1);

      expect(globalThis.fetch).toHaveBeenCalledWith(
        `${PERMISSIONS_API_BASE}/1`,
        {
          method: "DELETE",
          credentials: "include",
        },
      );
    });

    it("should throw error when permission not found", async () => {
      const mockResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue({
          detail: "permission_not_found",
        }),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(deletePermission(1)).rejects.toThrow(
        "Permission not found. It may have already been deleted.",
      );
    });

    it("should throw error when permission assigned to roles with count", async () => {
      const mockResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue({
          detail: "permission_assigned_to_roles_3",
        }),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(deletePermission(1)).rejects.toThrow(
        "Cannot delete permission. This permission is assigned to 3 role(s). Please remove the permission from all roles before deleting.",
      );
    });

    it("should throw error when permission assigned to roles (generic)", async () => {
      const mockResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue({
          detail: "cannot_delete_permission",
        }),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(deletePermission(1)).rejects.toThrow(
        "Cannot delete permission. This permission is associated with one or more roles.",
      );
    });
  });

  describe("updateRolePermission", () => {
    it("should update role permission successfully", async () => {
      const updateData = {
        condition: { key: "value" },
      };
      const mockRole = createMockRole(1);
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue(mockRole),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await updateRolePermission(1, 10, updateData);

      expect(globalThis.fetch).toHaveBeenCalledWith(
        `${apiBase}/1/permissions/10`,
        {
          method: "PUT",
          headers: baseHeaders,
          credentials: "include",
          body: JSON.stringify(updateData),
        },
      );
      expect(result).toEqual(mockRole);
    });

    it("should throw error when response is not ok", async () => {
      const updateData = {
        condition: { key: "value" },
      };
      const mockResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue({
          detail: "Role permission not found",
        }),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(updateRolePermission(1, 10, updateData)).rejects.toThrow(
        "Role permission not found",
      );
    });
  });
});
