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

import type { NewPermissionDetails } from "@/hooks/useRolePermissions";
import type { Permission, Role } from "@/services/roleService";

export interface PermissionAssignment {
  permission_id?: number | null;
  permission_name?: string | null;
  resource?: string | null;
  action?: string | null;
  permission_description?: string | null;
  condition?: Record<string, unknown> | null;
}

/**
 * Build permission assignments for role creation/update.
 *
 * Handles both existing permissions (by ID) and new permissions (with full details).
 * Follows SRP by focusing solely on permission assignment construction.
 * Follows DRY by centralizing assignment building logic.
 *
 * Parameters
 * ----------
 * existingPermissionNames : string[]
 *     Names of existing permissions to include.
 * newPermissionNames : string[]
 *     Names of new permissions to create.
 * permissionMap : Map<string, Permission>
 *     Map of permission names to Permission objects.
 * newPermissionDetails : Record<string, NewPermissionDetails>
 *     Details for new permissions.
 * role : Role | null | undefined
 *     Original role (for update mode to detect newly added permissions).
 * isEditMode : boolean
 *     Whether in edit mode.
 *
 * Returns
 * -------
 * PermissionAssignment[]
 *     Array of permission assignments.
 *
 * Throws
 * ------
 * Error
 *     If a new permission is missing required fields or has invalid JSON condition.
 */
export function buildPermissionAssignments(
  existingPermissionNames: string[],
  newPermissionNames: string[],
  permissionMap: Map<string, Permission>,
  newPermissionDetails: Record<string, NewPermissionDetails>,
  role?: Role | null,
  isEditMode = false,
): PermissionAssignment[] {
  const assignments: PermissionAssignment[] = [];

  if (isEditMode && role) {
    // In update mode, only send NEW permissions (ones not in original role)
    const originalPermissionIds = new Set(
      role.permissions.map((rp) => rp.permission.id),
    );

    // Process existing permissions that are NEW to the role
    for (const permName of existingPermissionNames) {
      const permission = permissionMap.get(permName);
      if (permission && !originalPermissionIds.has(permission.id)) {
        // This is an existing permission that's being added to the role
        assignments.push({
          permission_id: permission.id,
          condition: null,
        });
      }
    }
  } else {
    // In create mode, send all permissions
    // Process existing permissions (by name, they exist in the database)
    for (const permName of existingPermissionNames) {
      const permission = permissionMap.get(permName);
      if (permission) {
        assignments.push({
          permission_id: permission.id,
          condition: null,
        });
      }
    }
  }

  // Process new permissions (always send these as they need to be created)
  for (const permName of newPermissionNames) {
    const details = newPermissionDetails[permName];
    if (!details) {
      continue;
    }

    const resource = details.resource.trim();
    const action = details.action.trim();
    if (!resource || !action) {
      throw new Error(
        "All new permissions must have resource and action specified",
      );
    }

    // Parse condition JSON if provided
    let condition: Record<string, unknown> | null = null;
    if (details.condition.trim()) {
      try {
        condition = JSON.parse(details.condition.trim());
      } catch (err) {
        throw new Error(
          `Invalid JSON condition for permission "${permName}": ${
            err instanceof Error ? err.message : "Invalid JSON"
          }`,
        );
      }
    }

    assignments.push({
      permission_name: permName.trim(),
      resource,
      action,
      permission_description: details.description.trim() || null,
      condition,
    });
  }

  return assignments;
}

/**
 * Calculate removed permission IDs for role update.
 *
 * Compares original role permissions with current permission names
 * to determine which role_permission records should be removed.
 *
 * Parameters
 * ----------
 * role : Role
 *     Original role with permissions.
 * existingPermissionNames : string[]
 *     Current existing permission names.
 * permissionMap : Map<string, Permission>
 *     Map of permission names to Permission objects.
 *
 * Returns
 * -------
 * number[]
 *     Array of role_permission IDs to remove.
 */
export function calculateRemovedPermissionIds(
  role: Role,
  existingPermissionNames: string[],
  permissionMap: Map<string, Permission>,
): number[] {
  const currentPermissionIds = new Set(
    existingPermissionNames
      .map((name) => permissionMap.get(name)?.id)
      .filter((id): id is number => id !== undefined),
  );

  // Find role_permission IDs that need to be removed
  const permissionsToRemove: number[] = [];
  for (const rp of role.permissions) {
    // If the permission is no longer in the current list, mark it for removal
    if (!currentPermissionIds.has(rp.permission.id)) {
      permissionsToRemove.push(rp.id);
    }
  }

  return permissionsToRemove;
}
