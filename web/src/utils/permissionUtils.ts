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

import type {
  Permission,
  PermissionUpdate,
  Role,
} from "@/services/roleService";
import type { PermissionFormData } from "@/utils/permissionValidation";

/**
 * Build permission update object from form data.
 *
 * Only includes fields that have changed from the existing permission.
 * Follows DRY by centralizing permission update construction logic.
 *
 * Parameters
 * ----------
 * data : PermissionFormData
 *     Form data containing permission values.
 * existing : Permission
 *     Existing permission to compare against.
 *
 * Returns
 * -------
 * PermissionUpdate
 *     Update object with only changed fields.
 */
export function buildPermissionUpdate(
  data: PermissionFormData,
  existing: Permission,
): PermissionUpdate {
  return {
    name: data.name.trim() !== existing.name ? data.name.trim() : undefined,
    description:
      data.description.trim() !== (existing.description ?? "")
        ? data.description.trim() || null
        : undefined,
    resource:
      data.resource.trim() !== existing.resource
        ? data.resource.trim()
        : undefined,
    action:
      data.action.trim() !== existing.action ? data.action.trim() : undefined,
  };
}

/**
 * Check if permission update has any changes.
 *
 * Parameters
 * ----------
 * update : PermissionUpdate
 *     Permission update object to check.
 *
 * Returns
 * -------
 * boolean
 *     True if update contains any changes, false otherwise.
 */
export function hasPermissionChanges(update: PermissionUpdate): boolean {
  return Object.values(update).some((v) => v !== undefined);
}

/**
 * Merge permission update into role's permissions.
 *
 * Updates the permission data for a specific role-permission association.
 * Follows DRY by centralizing role update construction logic.
 *
 * Parameters
 * ----------
 * role : Role
 *     Role to update.
 * rolePermissionId : number
 *     ID of the role-permission association to update.
 * permissionUpdate : Partial<Permission>
 *     Permission fields to merge.
 *
 * Returns
 * -------
 * Role
 *     Updated role with merged permission data.
 */
export function mergePermissionIntoRole(
  role: Role,
  rolePermissionId: number,
  permissionUpdate: Partial<Permission>,
): Role {
  return {
    ...role,
    permissions: role.permissions.map((rp) =>
      rp.id === rolePermissionId
        ? {
            ...rp,
            permission: { ...rp.permission, ...permissionUpdate },
          }
        : rp,
    ),
  };
}

/**
 * Parse condition JSON string safely.
 *
 * Parameters
 * ----------
 * conditionString : string
 *     JSON string to parse.
 *
 * Returns
 * -------
 * Record<string, unknown> | null
 *     Parsed condition object, or null if empty/invalid.
 *
 * Throws
 * ------
 * Error
 *     If JSON string is invalid and non-empty.
 */
export function parseConditionJson(
  conditionString: string,
): Record<string, unknown> | null {
  const trimmed = conditionString.trim();
  if (!trimmed) {
    return null;
  }
  try {
    return JSON.parse(trimmed) as Record<string, unknown>;
  } catch (error) {
    throw new Error(
      error instanceof Error
        ? `Invalid JSON condition: ${error.message}`
        : "Invalid JSON condition format",
    );
  }
}
