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

import { useCallback } from "react";
import type {
  Permission,
  PermissionCreate,
  PermissionUpdate,
  Role,
  RolePermission,
  RolePermissionUpdate,
} from "@/services/roleService";
import {
  buildPermissionUpdate,
  hasPermissionChanges,
  mergePermissionIntoRole,
  parseConditionJson,
} from "@/utils/permissionUtils";
import type { PermissionFormData } from "@/utils/permissionValidation";

export interface PermissionSubmitOperations {
  /** Create a new permission. */
  createPermission: (data: PermissionCreate) => Promise<Permission>;
  /** Update an existing permission. */
  updatePermission: (id: number, data: PermissionUpdate) => Promise<Permission>;
  /** Update a role-permission association. */
  updateRolePermission: (
    roleId: number,
    rolePermissionId: number,
    data: RolePermissionUpdate,
  ) => Promise<Role>;
  /** Optimistically update role in context. */
  updateRoleOptimistic: (role: Role) => void;
}

export interface UsePermissionSubmitOptions {
  /** Whether we're in role context mode. */
  isRoleContext: boolean;
  /** Whether we're in edit mode. */
  isEditMode: boolean;
  /** Permission being edited (if any). */
  permission: Permission | null | undefined;
  /** Role-permission association (if in role context). */
  rolePermission: RolePermission | undefined;
  /** Role that owns the permission (if in role context). */
  role: Role | undefined;
  /** Permission operations (injected for IOC). */
  operations: PermissionSubmitOperations;
  /** Callback when save succeeds. */
  onSave: (data: Permission | Role) => void;
  /** Callback when save should be cancelled (no changes). */
  onCancel: () => void;
  /** Callback when an error occurs. */
  onError: (error: string) => void;
}

/**
 * Hook for permission form submission logic.
 *
 * Handles submission in both standalone and role context modes.
 * Follows SRP by separating submission logic from UI components.
 * Follows IOC by accepting operations as dependencies.
 * Follows DRY by reusing utility functions.
 *
 * Parameters
 * ----------
 * options : UsePermissionSubmitOptions
 *     Configuration options for submission.
 *
 * Returns
 * -------
 * function
 *     Submit handler function.
 */
export function usePermissionSubmit({
  isRoleContext,
  isEditMode,
  permission,
  rolePermission,
  role,
  operations,
  onSave,
  onCancel,
  onError,
}: UsePermissionSubmitOptions) {
  const handleSubmit = useCallback(
    async (data: PermissionFormData) => {
      try {
        if (isRoleContext && rolePermission && role && permission) {
          // Role context mode: update permission and role-permission condition
          await handleRoleContextSubmit(
            data,
            permission,
            rolePermission,
            role,
            operations,
            onSave,
            onCancel,
          );
        } else {
          // Standalone mode: create or update permission
          await handleStandaloneSubmit(
            data,
            isEditMode,
            permission,
            operations,
            onSave,
            onCancel,
          );
        }
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Failed to save permission";
        onError(errorMessage);
      }
    },
    [
      isRoleContext,
      isEditMode,
      permission,
      rolePermission,
      role,
      operations,
      onSave,
      onCancel,
      onError,
    ],
  );

  return handleSubmit;
}

/**
 * Handle submission in role context mode.
 *
 * Parameters
 * ----------
 * data : PermissionFormData
 *     Form data.
 * permission : Permission
 *     Existing permission.
 * rolePermission : RolePermission
 *     Role-permission association.
 * role : Role
 *     Role that owns the permission.
 * operations : PermissionSubmitOperations
 *     Permission operations.
 * onSave : function
 *     Callback when save succeeds.
 * onCancel : function
 *     Callback when no changes.
 */
async function handleRoleContextSubmit(
  data: PermissionFormData,
  permission: Permission,
  rolePermission: RolePermission,
  role: Role,
  operations: PermissionSubmitOperations,
  onSave: (data: Role) => void,
  onCancel: () => void,
): Promise<void> {
  // Parse condition JSON if provided
  let conditionObj: Record<string, unknown> | null = null;
  if (data.condition.trim()) {
    conditionObj = parseConditionJson(data.condition.trim());
  }

  // Build permission update
  const permissionUpdate = buildPermissionUpdate(data, permission);
  const hasPermissionChangesFlag = hasPermissionChanges(permissionUpdate);

  // Check if condition changed
  const currentCondition = rolePermission.condition
    ? JSON.stringify(rolePermission.condition, null, 2)
    : "";
  const conditionChanged = data.condition.trim() !== currentCondition;

  if (conditionChanged) {
    // Update condition (this returns the full updated role)
    const rolePermissionUpdate: RolePermissionUpdate = {
      condition: conditionObj,
    };
    const updatedRole = await operations.updateRolePermission(
      role.id,
      rolePermission.id,
      rolePermissionUpdate,
    );

    // If permission details also changed, update them and merge optimistically
    if (hasPermissionChangesFlag) {
      await operations.updatePermission(permission.id, permissionUpdate);
      // The role returned from updateRolePermission may not have the latest permission data
      // So we update it optimistically with the permission changes
      const roleWithUpdatedPermission = mergePermissionIntoRole(
        updatedRole,
        rolePermission.id,
        {
          name: permissionUpdate.name ?? permission.name,
          description:
            permissionUpdate.description !== undefined
              ? permissionUpdate.description
              : permission.description,
          resource: permissionUpdate.resource ?? permission.resource,
          action: permissionUpdate.action ?? permission.action,
        },
      );
      operations.updateRoleOptimistic(roleWithUpdatedPermission);
      onSave(roleWithUpdatedPermission);
    } else {
      // Only condition changed
      operations.updateRoleOptimistic(updatedRole);
      onSave(updatedRole);
    }
  } else if (hasPermissionChangesFlag) {
    // Only permission details changed, update permission and construct updated role
    await operations.updatePermission(permission.id, permissionUpdate);
    const updatedRole = mergePermissionIntoRole(role, rolePermission.id, {
      name: permissionUpdate.name ?? permission.name,
      description:
        permissionUpdate.description !== undefined
          ? permissionUpdate.description
          : permission.description,
      resource: permissionUpdate.resource ?? permission.resource,
      action: permissionUpdate.action ?? permission.action,
    });
    operations.updateRoleOptimistic(updatedRole);
    onSave(updatedRole);
  } else {
    // No changes
    onCancel();
  }
}

/**
 * Handle submission in standalone mode.
 *
 * Parameters
 * ----------
 * data : PermissionFormData
 *     Form data.
 * isEditMode : boolean
 *     Whether we're editing an existing permission.
 * permission : Permission | null | undefined
 *     Existing permission (if editing).
 * operations : PermissionSubmitOperations
 *     Permission operations.
 * onSave : function
 *     Callback when save succeeds.
 * onCancel : function
 *     Callback when no changes.
 */
async function handleStandaloneSubmit(
  data: PermissionFormData,
  isEditMode: boolean,
  permission: Permission | null | undefined,
  operations: PermissionSubmitOperations,
  onSave: (data: Permission) => void,
  onCancel: () => void,
): Promise<void> {
  if (isEditMode && permission) {
    // Update existing permission
    const permissionUpdate = buildPermissionUpdate(data, permission);
    const hasChanges = hasPermissionChanges(permissionUpdate);

    if (hasChanges) {
      const updatedPermission = await operations.updatePermission(
        permission.id,
        permissionUpdate,
      );
      onSave(updatedPermission);
    } else {
      // No changes
      onCancel();
    }
  } else {
    // Create new permission
    // Note: condition is not part of Permission, it's part of RolePermission
    // So we don't send condition when creating a standalone permission
    const newPermission = await operations.createPermission({
      name: data.name.trim(),
      description: data.description.trim() || null,
      resource: data.resource.trim(),
      action: data.action.trim(),
    });
    onSave(newPermission);
  }
}
