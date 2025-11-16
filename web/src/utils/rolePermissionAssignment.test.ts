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

import { describe, expect, it } from "vitest";
import type { NewPermissionDetails } from "@/hooks/useRolePermissions";
import type { Permission, Role } from "@/services/roleService";
import {
  buildPermissionAssignments,
  calculateRemovedPermissionIds,
} from "./rolePermissionAssignment";

describe("rolePermissionAssignment utils", () => {
  const createMockPermission = (
    id: number,
    name: string,
    resource: string,
    action: string,
  ): Permission => ({
    id,
    name,
    description: `Description for ${name}`,
    resource,
    action,
  });

  const createMockRole = (id: number, permissionIds: number[]): Role => {
    const permissions = permissionIds.map((permId) => ({
      id: permId * 10, // role_permission ID
      permission: createMockPermission(
        permId,
        `permission-${permId}`,
        `resource-${permId}`,
        `action-${permId}`,
      ),
      condition: null,
      assigned_at: "2024-01-01T00:00:00Z",
    }));

    return {
      id,
      name: `role-${id}`,
      description: `Description for role-${id}`,
      permissions,
    };
  };

  describe("buildPermissionAssignments", () => {
    it("should build assignments for create mode with existing permissions", () => {
      const existingPermissionNames = ["permission-1", "permission-2"];
      const newPermissionNames: string[] = [];
      const permissionMap = new Map<string, Permission>([
        [
          "permission-1",
          createMockPermission(1, "permission-1", "resource-1", "action-1"),
        ],
        [
          "permission-2",
          createMockPermission(2, "permission-2", "resource-2", "action-2"),
        ],
      ]);
      const newPermissionDetails: Record<string, NewPermissionDetails> = {};

      const assignments = buildPermissionAssignments(
        existingPermissionNames,
        newPermissionNames,
        permissionMap,
        newPermissionDetails,
        null,
        false,
      );

      expect(assignments).toHaveLength(2);
      expect(assignments[0]).toEqual({
        permission_id: 1,
        condition: null,
      });
      expect(assignments[1]).toEqual({
        permission_id: 2,
        condition: null,
      });
    });

    it("should build assignments for create mode with new permissions", () => {
      const existingPermissionNames: string[] = [];
      const newPermissionNames = ["new-permission-1"];
      const permissionMap = new Map<string, Permission>();
      const newPermissionDetails: Record<string, NewPermissionDetails> = {
        "new-permission-1": {
          description: "New permission description",
          resource: "new-resource",
          action: "new-action",
          condition: "",
        },
      };

      const assignments = buildPermissionAssignments(
        existingPermissionNames,
        newPermissionNames,
        permissionMap,
        newPermissionDetails,
        null,
        false,
      );

      expect(assignments).toHaveLength(1);
      expect(assignments[0]).toEqual({
        permission_name: "new-permission-1",
        resource: "new-resource",
        action: "new-action",
        permission_description: "New permission description",
        condition: null,
      });
    });

    it("should build assignments for create mode with both existing and new permissions", () => {
      const existingPermissionNames = ["permission-1"];
      const newPermissionNames = ["new-permission-1"];
      const permissionMap = new Map<string, Permission>([
        [
          "permission-1",
          createMockPermission(1, "permission-1", "resource-1", "action-1"),
        ],
      ]);
      const newPermissionDetails: Record<string, NewPermissionDetails> = {
        "new-permission-1": {
          description: "New permission description",
          resource: "new-resource",
          action: "new-action",
          condition: "",
        },
      };

      const assignments = buildPermissionAssignments(
        existingPermissionNames,
        newPermissionNames,
        permissionMap,
        newPermissionDetails,
        null,
        false,
      );

      expect(assignments).toHaveLength(2);
      expect(assignments[0]).toEqual({
        permission_id: 1,
        condition: null,
      });
      expect(assignments[1]).toEqual({
        permission_name: "new-permission-1",
        resource: "new-resource",
        action: "new-action",
        permission_description: "New permission description",
        condition: null,
      });
    });

    it("should build assignments for edit mode with only new permissions", () => {
      const role = createMockRole(1, [1, 2]);
      const existingPermissionNames = [
        "permission-1",
        "permission-2",
        "permission-3",
      ];
      const newPermissionNames: string[] = [];
      const permissionMap = new Map<string, Permission>([
        [
          "permission-1",
          createMockPermission(1, "permission-1", "resource-1", "action-1"),
        ],
        [
          "permission-2",
          createMockPermission(2, "permission-2", "resource-2", "action-2"),
        ],
        [
          "permission-3",
          createMockPermission(3, "permission-3", "resource-3", "action-3"),
        ],
      ]);
      const newPermissionDetails: Record<string, NewPermissionDetails> = {};

      const assignments = buildPermissionAssignments(
        existingPermissionNames,
        newPermissionNames,
        permissionMap,
        newPermissionDetails,
        role,
        true,
      );

      // Only permission-3 should be included (it's new to the role)
      expect(assignments).toHaveLength(1);
      expect(assignments[0]).toEqual({
        permission_id: 3,
        condition: null,
      });
    });

    it("should not include existing permissions already in role for edit mode", () => {
      const role = createMockRole(1, [1, 2]);
      const existingPermissionNames = ["permission-1", "permission-2"];
      const newPermissionNames: string[] = [];
      const permissionMap = new Map<string, Permission>([
        [
          "permission-1",
          createMockPermission(1, "permission-1", "resource-1", "action-1"),
        ],
        [
          "permission-2",
          createMockPermission(2, "permission-2", "resource-2", "action-2"),
        ],
      ]);
      const newPermissionDetails: Record<string, NewPermissionDetails> = {};

      const assignments = buildPermissionAssignments(
        existingPermissionNames,
        newPermissionNames,
        permissionMap,
        newPermissionDetails,
        role,
        true,
      );

      // No new permissions to add
      expect(assignments).toHaveLength(0);
    });

    it("should handle new permissions with condition JSON in create mode", () => {
      const existingPermissionNames: string[] = [];
      const newPermissionNames = ["new-permission-1"];
      const permissionMap = new Map<string, Permission>();
      const newPermissionDetails: Record<string, NewPermissionDetails> = {
        "new-permission-1": {
          description: "New permission description",
          resource: "new-resource",
          action: "new-action",
          condition: '{"key": "value"}',
        },
      };

      const assignments = buildPermissionAssignments(
        existingPermissionNames,
        newPermissionNames,
        permissionMap,
        newPermissionDetails,
        null,
        false,
      );

      expect(assignments).toHaveLength(1);
      expect(assignments[0]).toEqual({
        permission_name: "new-permission-1",
        resource: "new-resource",
        action: "new-action",
        permission_description: "New permission description",
        condition: { key: "value" },
      });
    });

    it("should handle new permissions with condition JSON in edit mode", () => {
      const role = createMockRole(1, [1]);
      const existingPermissionNames = ["permission-1"];
      const newPermissionNames = ["new-permission-1"];
      const permissionMap = new Map<string, Permission>([
        [
          "permission-1",
          createMockPermission(1, "permission-1", "resource-1", "action-1"),
        ],
      ]);
      const newPermissionDetails: Record<string, NewPermissionDetails> = {
        "new-permission-1": {
          description: "New permission description",
          resource: "new-resource",
          action: "new-action",
          condition: '{"nested": {"key": 123}}',
        },
      };

      const assignments = buildPermissionAssignments(
        existingPermissionNames,
        newPermissionNames,
        permissionMap,
        newPermissionDetails,
        role,
        true,
      );

      expect(assignments).toHaveLength(1);
      expect(assignments[0]?.condition).toEqual({ nested: { key: 123 } });
    });

    it("should trim whitespace from new permission fields", () => {
      const existingPermissionNames: string[] = [];
      const newPermissionNames = ["  new-permission-1  "];
      const permissionMap = new Map<string, Permission>();
      const newPermissionDetails: Record<string, NewPermissionDetails> = {
        "  new-permission-1  ": {
          description: "  Description  ",
          resource: "  resource  ",
          action: "  action  ",
          condition: "",
        },
      };

      const assignments = buildPermissionAssignments(
        existingPermissionNames,
        newPermissionNames,
        permissionMap,
        newPermissionDetails,
        null,
        false,
      );

      expect(assignments).toHaveLength(1);
      expect(assignments[0]?.permission_name).toBe("new-permission-1");
      expect(assignments[0]?.resource).toBe("resource");
      expect(assignments[0]?.action).toBe("action");
      expect(assignments[0]?.permission_description).toBe("Description");
    });

    it("should set description to null if empty after trim", () => {
      const existingPermissionNames: string[] = [];
      const newPermissionNames = ["new-permission-1"];
      const permissionMap = new Map<string, Permission>();
      const newPermissionDetails: Record<string, NewPermissionDetails> = {
        "new-permission-1": {
          description: "   ",
          resource: "resource",
          action: "action",
          condition: "",
        },
      };

      const assignments = buildPermissionAssignments(
        existingPermissionNames,
        newPermissionNames,
        permissionMap,
        newPermissionDetails,
        null,
        false,
      );

      expect(assignments[0]?.permission_description).toBeNull();
    });

    it("should throw error if new permission is missing resource", () => {
      const existingPermissionNames: string[] = [];
      const newPermissionNames = ["new-permission-1"];
      const permissionMap = new Map<string, Permission>();
      const newPermissionDetails: Record<string, NewPermissionDetails> = {
        "new-permission-1": {
          description: "Description",
          resource: "",
          action: "action",
          condition: "",
        },
      };

      expect(() =>
        buildPermissionAssignments(
          existingPermissionNames,
          newPermissionNames,
          permissionMap,
          newPermissionDetails,
          null,
          false,
        ),
      ).toThrow("All new permissions must have resource and action specified");
    });

    it("should throw error if new permission is missing action", () => {
      const existingPermissionNames: string[] = [];
      const newPermissionNames = ["new-permission-1"];
      const permissionMap = new Map<string, Permission>();
      const newPermissionDetails: Record<string, NewPermissionDetails> = {
        "new-permission-1": {
          description: "Description",
          resource: "resource",
          action: "",
          condition: "",
        },
      };

      expect(() =>
        buildPermissionAssignments(
          existingPermissionNames,
          newPermissionNames,
          permissionMap,
          newPermissionDetails,
          null,
          false,
        ),
      ).toThrow("All new permissions must have resource and action specified");
    });

    it("should throw error if new permission has invalid JSON condition", () => {
      const existingPermissionNames: string[] = [];
      const newPermissionNames = ["new-permission-1"];
      const permissionMap = new Map<string, Permission>();
      const newPermissionDetails: Record<string, NewPermissionDetails> = {
        "new-permission-1": {
          description: "Description",
          resource: "resource",
          action: "action",
          condition: "{invalid json}",
        },
      };

      expect(() =>
        buildPermissionAssignments(
          existingPermissionNames,
          newPermissionNames,
          permissionMap,
          newPermissionDetails,
          null,
          false,
        ),
      ).toThrow(/Invalid JSON condition for permission "new-permission-1"/);
    });

    it("should handle non-Error exceptions in JSON parsing", () => {
      const existingPermissionNames: string[] = [];
      const newPermissionNames = ["new-permission-1"];
      const permissionMap = new Map<string, Permission>();
      const newPermissionDetails: Record<string, NewPermissionDetails> = {
        "new-permission-1": {
          description: "Description",
          resource: "resource",
          action: "action",
          condition: "{}",
        },
      };

      // Mock JSON.parse to throw a non-Error
      const originalParse = JSON.parse;
      JSON.parse = () => {
        throw "string error";
      };

      expect(() =>
        buildPermissionAssignments(
          existingPermissionNames,
          newPermissionNames,
          permissionMap,
          newPermissionDetails,
          null,
          false,
        ),
      ).toThrow(/Invalid JSON condition for permission "new-permission-1"/);

      // Restore original
      JSON.parse = originalParse;
    });

    it("should skip new permissions without details", () => {
      const existingPermissionNames: string[] = [];
      const newPermissionNames = ["new-permission-1", "new-permission-2"];
      const permissionMap = new Map<string, Permission>();
      const newPermissionDetails: Record<string, NewPermissionDetails> = {
        "new-permission-1": {
          description: "Description",
          resource: "resource",
          action: "action",
          condition: "",
        },
      };

      const assignments = buildPermissionAssignments(
        existingPermissionNames,
        newPermissionNames,
        permissionMap,
        newPermissionDetails,
        null,
        false,
      );

      expect(assignments).toHaveLength(1);
      expect(assignments[0]?.permission_name).toBe("new-permission-1");
    });

    it("should handle missing permission in map gracefully", () => {
      const existingPermissionNames = ["permission-1", "permission-missing"];
      const newPermissionNames: string[] = [];
      const permissionMap = new Map<string, Permission>([
        [
          "permission-1",
          createMockPermission(1, "permission-1", "resource-1", "action-1"),
        ],
      ]);
      const newPermissionDetails: Record<string, NewPermissionDetails> = {};

      const assignments = buildPermissionAssignments(
        existingPermissionNames,
        newPermissionNames,
        permissionMap,
        newPermissionDetails,
        null,
        false,
      );

      // Only permission-1 should be included (permission-missing is not in map)
      expect(assignments).toHaveLength(1);
      expect(assignments[0]?.permission_id).toBe(1);
    });

    it("should handle edit mode with role but no new existing permissions", () => {
      const role = createMockRole(1, [1, 2]);
      const existingPermissionNames = ["permission-1", "permission-2"];
      const newPermissionNames: string[] = [];
      const permissionMap = new Map<string, Permission>([
        [
          "permission-1",
          createMockPermission(1, "permission-1", "resource-1", "action-1"),
        ],
        [
          "permission-2",
          createMockPermission(2, "permission-2", "resource-2", "action-2"),
        ],
      ]);
      const newPermissionDetails: Record<string, NewPermissionDetails> = {};

      const assignments = buildPermissionAssignments(
        existingPermissionNames,
        newPermissionNames,
        permissionMap,
        newPermissionDetails,
        role,
        true,
      );

      expect(assignments).toHaveLength(0);
    });

    it("should handle edit mode without role", () => {
      const existingPermissionNames = ["permission-1"];
      const newPermissionNames: string[] = [];
      const permissionMap = new Map<string, Permission>([
        [
          "permission-1",
          createMockPermission(1, "permission-1", "resource-1", "action-1"),
        ],
      ]);
      const newPermissionDetails: Record<string, NewPermissionDetails> = {};

      const assignments = buildPermissionAssignments(
        existingPermissionNames,
        newPermissionNames,
        permissionMap,
        newPermissionDetails,
        null,
        true,
      );

      // Should behave like create mode when role is null
      expect(assignments).toHaveLength(1);
      expect(assignments[0]?.permission_id).toBe(1);
    });
  });

  describe("calculateRemovedPermissionIds", () => {
    it("should return empty array when no permissions are removed", () => {
      const role = createMockRole(1, [1, 2]);
      const existingPermissionNames = ["permission-1", "permission-2"];
      const permissionMap = new Map<string, Permission>([
        [
          "permission-1",
          createMockPermission(1, "permission-1", "resource-1", "action-1"),
        ],
        [
          "permission-2",
          createMockPermission(2, "permission-2", "resource-2", "action-2"),
        ],
      ]);

      const removedIds = calculateRemovedPermissionIds(
        role,
        existingPermissionNames,
        permissionMap,
      );

      expect(removedIds).toEqual([]);
    });

    it("should return role_permission IDs for removed permissions", () => {
      const role = createMockRole(1, [1, 2, 3]);
      const existingPermissionNames = ["permission-1", "permission-2"];
      const permissionMap = new Map<string, Permission>([
        [
          "permission-1",
          createMockPermission(1, "permission-1", "resource-1", "action-1"),
        ],
        [
          "permission-2",
          createMockPermission(2, "permission-2", "resource-2", "action-2"),
        ],
        [
          "permission-3",
          createMockPermission(3, "permission-3", "resource-3", "action-3"),
        ],
      ]);

      const removedIds = calculateRemovedPermissionIds(
        role,
        existingPermissionNames,
        permissionMap,
      );

      // permission-3 was removed, so role_permission ID 30 should be returned
      expect(removedIds).toEqual([30]);
    });

    it("should return multiple role_permission IDs for multiple removed permissions", () => {
      const role = createMockRole(1, [1, 2, 3, 4]);
      const existingPermissionNames = ["permission-1"];
      const permissionMap = new Map<string, Permission>([
        [
          "permission-1",
          createMockPermission(1, "permission-1", "resource-1", "action-1"),
        ],
        [
          "permission-2",
          createMockPermission(2, "permission-2", "resource-2", "action-2"),
        ],
        [
          "permission-3",
          createMockPermission(3, "permission-3", "resource-3", "action-3"),
        ],
        [
          "permission-4",
          createMockPermission(4, "permission-4", "resource-4", "action-4"),
        ],
      ]);

      const removedIds = calculateRemovedPermissionIds(
        role,
        existingPermissionNames,
        permissionMap,
      );

      // permission-2, permission-3, and permission-4 were removed
      expect(removedIds).toHaveLength(3);
      expect(removedIds).toContain(20); // role_permission ID for permission-2
      expect(removedIds).toContain(30); // role_permission ID for permission-3
      expect(removedIds).toContain(40); // role_permission ID for permission-4
    });

    it("should handle permissions not in permissionMap", () => {
      const role = createMockRole(1, [1, 2]);
      const existingPermissionNames = ["permission-1", "permission-missing"];
      const permissionMap = new Map<string, Permission>([
        [
          "permission-1",
          createMockPermission(1, "permission-1", "resource-1", "action-1"),
        ],
      ]);

      const removedIds = calculateRemovedPermissionIds(
        role,
        existingPermissionNames,
        permissionMap,
      );

      // permission-2 is not in existingPermissionNames, so it should be removed
      expect(removedIds).toEqual([20]); // role_permission ID for permission-2
    });

    it("should return all role_permission IDs when all permissions are removed", () => {
      const role = createMockRole(1, [1, 2, 3]);
      const existingPermissionNames: string[] = [];
      const permissionMap = new Map<string, Permission>([
        [
          "permission-1",
          createMockPermission(1, "permission-1", "resource-1", "action-1"),
        ],
        [
          "permission-2",
          createMockPermission(2, "permission-2", "resource-2", "action-2"),
        ],
        [
          "permission-3",
          createMockPermission(3, "permission-3", "resource-3", "action-3"),
        ],
      ]);

      const removedIds = calculateRemovedPermissionIds(
        role,
        existingPermissionNames,
        permissionMap,
      );

      expect(removedIds).toHaveLength(3);
      expect(removedIds).toContain(10);
      expect(removedIds).toContain(20);
      expect(removedIds).toContain(30);
    });
  });
});
