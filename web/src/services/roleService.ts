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

/**
 * Service for interacting with admin role API endpoints.
 *
 * Provides methods for fetching, creating, updating, and deleting roles.
 */

import { deduplicateFetch } from "@/utils/fetch";

export interface Permission {
  id: number;
  name: string;
  description: string | null;
  resource: string;
  action: string;
}

export interface RolePermission {
  id: number;
  permission: Permission;
  condition: Record<string, unknown> | null;
  assigned_at: string;
}

export interface Role {
  id: number;
  name: string;
  description: string | null;
  permissions: RolePermission[];
  locked?: boolean;
}

export interface PermissionAssignment {
  permission_id?: number | null;
  permission_name?: string | null;
  resource?: string | null;
  action?: string | null;
  permission_description?: string | null;
  condition?: Record<string, unknown> | null;
}

export interface PermissionCreate {
  name: string;
  description?: string | null;
  resource: string;
  action: string;
  condition?: Record<string, unknown> | null;
}

export interface PermissionUpdate {
  name?: string | null;
  description?: string | null;
  resource?: string | null;
  action?: string | null;
}

export interface RolePermissionUpdate {
  condition?: Record<string, unknown> | null;
}

export interface RoleCreate {
  name: string;
  description?: string | null;
  permissions?: PermissionAssignment[];
}

export interface RoleUpdate {
  name?: string;
  description?: string | null;
  permissions?: PermissionAssignment[] | null;
  removed_permission_ids?: number[];
}

const API_BASE = "/api/admin/roles";
const PERMISSIONS_API_BASE = "/api/admin/permissions";

/**
 * Fetch all permissions.
 *
 * Uses fetch deduplication to prevent multiple simultaneous requests.
 * Returns empty array if endpoint is not available (graceful degradation).
 *
 * Returns
 * -------
 * Promise<Permission[]>
 *     List of all permissions, or empty array if endpoint is unavailable.
 */
export async function fetchPermissions(): Promise<Permission[]> {
  return deduplicateFetch(PERMISSIONS_API_BASE, async () => {
    try {
      const response = await fetch(PERMISSIONS_API_BASE, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      });

      if (!response.ok) {
        // If endpoint doesn't exist (404) or other error, return empty array
        // This allows frontend to work before backend is fully implemented
        if (response.status === 404) {
          console.warn(
            "Permissions endpoint not found. Returning empty array. Backend may not be implemented yet.",
          );
          return [];
        }
        const error = await response
          .json()
          .catch(() => ({ detail: "Failed to fetch permissions" }));
        console.warn(
          "Failed to fetch permissions:",
          error.detail || "Unknown error",
        );
        return [];
      }

      return response.json();
    } catch (err) {
      // Network errors or other exceptions - return empty array gracefully
      console.warn("Error fetching permissions:", err);
      return [];
    }
  });
}

/**
 * Fetch all roles.
 *
 * Uses fetch deduplication to prevent multiple simultaneous requests.
 *
 * Returns
 * -------
 * Promise<Role[]>
 *     List of all roles.
 */
export async function fetchRoles(): Promise<Role[]> {
  return deduplicateFetch(API_BASE, async () => {
    const response = await fetch(API_BASE, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: "Failed to fetch roles" }));
      throw new Error(error.detail || "Failed to fetch roles");
    }

    return response.json();
  });
}

/**
 * Create a new role.
 *
 * Parameters
 * ----------
 * data : RoleCreate
 *     Role creation data.
 *
 * Returns
 * -------
 * Promise<Role>
 *     Created role data.
 */
export async function createRole(data: RoleCreate): Promise<Role> {
  const response = await fetch(API_BASE, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to create role" }));
    throw new Error(error.detail || "Failed to create role");
  }

  return response.json();
}

/**
 * Update a role.
 *
 * Parameters
 * ----------
 * roleId : number
 *     Role ID to update.
 * data : RoleUpdate
 *     Role update data.
 *
 * Returns
 * -------
 * Promise<Role>
 *     Updated role data.
 */
export async function updateRole(
  roleId: number,
  data: RoleUpdate,
): Promise<Role> {
  const response = await fetch(`${API_BASE}/${roleId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to update role" }));
    throw new Error(error.detail || "Failed to update role");
  }

  return response.json();
}

/**
 * Delete a role.
 *
 * Parameters
 * ----------
 * roleId : number
 *     Role ID to delete.
 *
 * Returns
 * -------
 * Promise<void>
 */
export async function deleteRole(roleId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/${roleId}`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to delete role" }));

    // Map backend error codes to user-friendly messages
    const errorDetail = error.detail || "Failed to delete role";
    let userMessage = errorDetail;

    if (errorDetail === "cannot_delete_locked_role") {
      userMessage =
        "Cannot delete locked role. Locked roles cannot be deleted.";
    } else if (errorDetail === "role_assigned_to_users") {
      userMessage =
        "Cannot delete role. This role is assigned to one or more users. Please remove the role from all users before deleting.";
    } else if (errorDetail === "role_not_found") {
      userMessage = "Role not found. It may have already been deleted.";
    }

    throw new Error(userMessage);
  }
}

/**
 * Create a new permission.
 *
 * Parameters
 * ----------
 * data : PermissionCreate
 *     Permission creation data.
 *
 * Returns
 * -------
 * Promise<Permission>
 *     Created permission data.
 */
export async function createPermission(
  data: PermissionCreate,
): Promise<Permission> {
  const response = await fetch(PERMISSIONS_API_BASE, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to create permission" }));
    throw new Error(error.detail || "Failed to create permission");
  }

  return response.json();
}

/**
 * Update a permission.
 *
 * Parameters
 * ----------
 * permissionId : number
 *     Permission ID to update.
 * data : PermissionUpdate
 *     Permission update data.
 *
 * Returns
 * -------
 * Promise<Permission>
 *     Updated permission data.
 */
export async function updatePermission(
  permissionId: number,
  data: PermissionUpdate,
): Promise<Permission> {
  const response = await fetch(`${PERMISSIONS_API_BASE}/${permissionId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to update permission" }));
    throw new Error(error.detail || "Failed to update permission");
  }

  return response.json();
}

/**
 * Delete a permission.
 *
 * Only allows deletion of orphaned permissions (permissions with no role associations).
 *
 * Parameters
 * ----------
 * permissionId : number
 *     Permission ID to delete.
 *
 * Returns
 * -------
 * Promise<void>
 *
 * Throws
 * ------
 * Error
 *     If permission not found or if permission is associated with roles.
 */
export async function deletePermission(permissionId: number): Promise<void> {
  const response = await fetch(`${PERMISSIONS_API_BASE}/${permissionId}`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to delete permission" }));

    // Map backend error codes to user-friendly messages
    const errorDetail = error.detail || "Failed to delete permission";
    let userMessage = errorDetail;

    if (errorDetail === "permission_not_found") {
      userMessage = "Permission not found. It may have already been deleted.";
    } else if (errorDetail.startsWith("permission_assigned_to_roles_")) {
      const roleCount = errorDetail.replace(
        "permission_assigned_to_roles_",
        "",
      );
      userMessage = `Cannot delete permission. This permission is assigned to ${roleCount} role(s). Please remove the permission from all roles before deleting.`;
    } else if (errorDetail === "cannot_delete_permission") {
      userMessage =
        "Cannot delete permission. This permission is associated with one or more roles.";
    }

    throw new Error(userMessage);
  }
}

/**
 * Update a role-permission association condition.
 *
 * Parameters
 * ----------
 * roleId : number
 *     Role ID.
 * rolePermissionId : number
 *     Role-permission association ID.
 * data : RolePermissionUpdate
 *     Update data with condition.
 *
 * Returns
 * -------
 * Promise<Role>
 *     Updated role data.
 */
export async function updateRolePermission(
  roleId: number,
  rolePermissionId: number,
  data: RolePermissionUpdate,
): Promise<Role> {
  const response = await fetch(
    `${API_BASE}/${roleId}/permissions/${rolePermissionId}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify(data),
    },
  );

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to update role permission" }));
    throw new Error(error.detail || "Failed to update role permission");
  }

  return response.json();
}
