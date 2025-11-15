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

"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/forms/Button";
import { useRoles } from "@/contexts/RolesContext";
import { useDeleteConfirmationState } from "@/hooks/useDeleteConfirmationState";
import { useModalState } from "@/hooks/useModalState";
import { useRoleManagement } from "@/hooks/useRoleManagement";
import { useUserManagement } from "@/hooks/useUserManagement";
import type {
  Permission,
  Role,
  RoleCreate,
  RolePermission,
  RoleUpdate,
} from "@/services/roleService";
import { deletePermission, fetchPermissions } from "@/services/roleService";
import type { UserCreate, UserUpdate } from "@/services/userService";
import { DeletePermissionConfirmationModal } from "../DeletePermissionConfirmationModal";
import { DeleteRoleConfirmationModal } from "../DeleteRoleConfirmationModal";
import { DeleteUserConfirmationModal } from "../DeleteUserConfirmationModal";
import { PermissionEditModal } from "../PermissionEditModal";
import { PermissionsTable } from "../PermissionsTable";
import { RoleEditModal } from "../RoleEditModal";
import { RolesTable } from "../RolesTable";
import { UserEditModal } from "../UserEditModal";
import { type User, UsersTable } from "../UsersTable";

/**
 * Users and Roles tab component.
 *
 * Manages users and roles in the admin panel.
 * Follows SRP by delegating concerns to specialized hooks.
 * Follows IOC by accepting callbacks for all operations.
 * Uses DRY by leveraging useUserManagement, useRoleManagement, and modal state hooks.
 */
export function UsersAndRolesTab() {
  // User management (SRP via hook)
  const {
    users,
    isLoading,
    handleCreate: createUser,
    handleUpdate: updateUser,
    handleDelete: deleteUser,
  } = useUserManagement();

  // Role management (SRP via hook)
  const roleManagement = useRoleManagement();
  const { refresh: refreshRoles } = useRoles();

  // Roles context for reading roles list
  const { roles, isLoading: isLoadingRoles } = useRoles();

  // User modal state (DRY via hook)
  const userModal = useModalState<User>();
  const userDeleteState = useDeleteConfirmationState<User>();

  // Role modal state (DRY via hook)
  const roleModal = useModalState<Role>();
  const roleDeleteState = useDeleteConfirmationState<Role>();

  // Permission edit modal state
  const [selectedRolePermission, setSelectedRolePermission] =
    useState<RolePermission | null>(null);
  const [showPermissionEditModal, setShowPermissionEditModal] = useState(false);

  // Standalone permission management state
  const permissionModal = useModalState<Permission>();
  const permissionDeleteState = useDeleteConfirmationState<Permission>();
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [isLoadingPermissions, setIsLoadingPermissions] = useState(false);

  // Load permissions
  useEffect(() => {
    const loadPermissions = async () => {
      setIsLoadingPermissions(true);
      try {
        const fetchedPermissions = await fetchPermissions();
        setPermissions(fetchedPermissions);
      } catch (err) {
        console.error("Failed to fetch permissions:", err);
      } finally {
        setIsLoadingPermissions(false);
      }
    };

    void loadPermissions();
  }, []);

  // Permission handlers (standalone mode)
  const handleSavePermission = useCallback(
    async (data: Permission | Role): Promise<void> => {
      // In standalone mode, data is a Permission
      if ("resource" in data && "action" in data && !("permissions" in data)) {
        const savedPermission = data as Permission;
        // Update local state
        if (permissionModal.selectedItem) {
          setPermissions((prev) =>
            prev.map((p) =>
              p.id === savedPermission.id ? savedPermission : p,
            ),
          );
        } else {
          setPermissions((prev) => [...prev, savedPermission]);
        }
      }
      // In role context mode, data is a Role (handled by handleSaveRolePermission)
      permissionModal.close();
    },
    [permissionModal],
  );

  const handleConfirmDeletePermission = useCallback(async () => {
    if (!permissionDeleteState.itemToDelete) {
      return;
    }

    const permissionToDelete = permissionDeleteState.itemToDelete;

    permissionDeleteState.setIsDeleting(true);
    permissionDeleteState.setError(null);

    try {
      await deletePermission(permissionToDelete.id);
      // Remove from local state
      setPermissions((prev) =>
        prev.filter((p) => p.id !== permissionToDelete.id),
      );
      // Refresh roles to ensure consistency
      await refreshRoles();
      permissionDeleteState.close();
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to delete permission";
      permissionDeleteState.setError(errorMessage);
    } finally {
      permissionDeleteState.setIsDeleting(false);
    }
  }, [permissionDeleteState, refreshRoles]);

  // User handlers
  const handleSaveUser = useCallback(
    async (data: UserCreate | UserUpdate): Promise<User> => {
      const savedUser = userModal.selectedItem
        ? await updateUser(userModal.selectedItem.id, data)
        : await createUser(data as UserCreate);
      userModal.close();
      return savedUser;
    },
    [userModal, createUser, updateUser],
  );

  const handleConfirmDeleteUser = useCallback(async () => {
    if (!userDeleteState.itemToDelete) return;

    userDeleteState.setIsDeleting(true);
    userDeleteState.setError(null);

    try {
      await deleteUser(userDeleteState.itemToDelete.id);
      userDeleteState.close();
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to delete user";
      userDeleteState.setError(errorMessage);
    } finally {
      userDeleteState.setIsDeleting(false);
    }
  }, [userDeleteState, deleteUser]);

  // Role handlers
  const handleSaveRole = useCallback(
    async (data: RoleCreate | RoleUpdate): Promise<Role> => {
      const savedRole = roleModal.selectedItem
        ? await roleManagement.handleUpdate(roleModal.selectedItem.id, data)
        : await roleManagement.handleCreate(data as RoleCreate);
      roleModal.close();
      return savedRole;
    },
    [roleModal, roleManagement],
  );

  const handleConfirmDeleteRole = useCallback(async () => {
    if (!roleDeleteState.itemToDelete) return;

    roleDeleteState.setIsDeleting(true);
    roleDeleteState.setError(null);

    try {
      await roleManagement.handleDelete(roleDeleteState.itemToDelete.id);
      roleDeleteState.close();
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to delete role";
      roleDeleteState.setError(errorMessage);
    } finally {
      roleDeleteState.setIsDeleting(false);
    }
  }, [roleDeleteState, roleManagement]);

  // Check if a role is assigned to any users
  const isRoleAssignedToUsers = useCallback(
    (roleId: number): boolean => {
      return users.some((user) => user.roles.some((r) => r.id === roleId));
    },
    [users],
  );

  // Permission edit handlers (for role-permission associations)
  const handlePermissionClick = useCallback(
    (role: Role, rolePermission: RolePermission) => {
      roleModal.openEdit(role);
      setSelectedRolePermission(rolePermission);
      setShowPermissionEditModal(true);
    },
    [roleModal],
  );

  const handleSaveRolePermission = useCallback(
    (updatedRole: Role) => {
      roleManagement.updateRoleOptimistic(updatedRole);
      setShowPermissionEditModal(false);
      roleModal.close();
      setSelectedRolePermission(null);
    },
    [roleManagement, roleModal],
  );

  return (
    <>
      <div className="flex flex-col gap-6">
        <div className="rounded-md border border-surface-a20 bg-surface-tonal-a0 p-6">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-4">
            <div className="flex min-w-0 flex-1 flex-col gap-1">
              <h2 className="font-semibold text-text-a0 text-xl">Users</h2>
              <p className="text-sm text-text-a30 leading-relaxed">
                Create, edit, and delete user accounts. Assign roles to control
                access permissions.
              </p>
            </div>
            <Button
              type="button"
              variant="primary"
              size="xsmall"
              onClick={userModal.openCreate}
              className="flex-shrink-0"
            >
              <i className="pi pi-plus" aria-hidden="true" />
              Add user
            </Button>
          </div>
          <UsersTable
            users={users}
            isLoading={isLoading}
            onEdit={userModal.openEdit}
            onDelete={userDeleteState.openDelete}
          />
        </div>

        <div className="rounded-md border border-surface-a20 bg-surface-tonal-a0 p-6">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-4">
            <div className="flex min-w-0 flex-1 flex-col gap-1">
              <h2 className="font-semibold text-text-a0 text-xl">Roles</h2>
              <p className="text-sm text-text-a30 leading-relaxed">
                Manage roles and their permissions. Locked roles and roles
                assigned to users cannot be deleted.
              </p>
            </div>
            <Button
              type="button"
              variant="primary"
              size="xsmall"
              onClick={roleModal.openCreate}
              className="flex-shrink-0"
            >
              <i className="pi pi-plus" aria-hidden="true" />
              Add role
            </Button>
          </div>
          <RolesTable
            roles={roles}
            isLoading={isLoadingRoles}
            onEdit={roleModal.openEdit}
            onDelete={roleDeleteState.openDelete}
            onPermissionClick={handlePermissionClick}
            isRoleAssignedToUsers={isRoleAssignedToUsers}
          />
        </div>

        {/* Permissions Management Section */}
        <div className="rounded-md border border-surface-a20 bg-surface-tonal-a0 p-6">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-4">
            <div className="flex min-w-0 flex-1 flex-col gap-1">
              <h2 className="font-semibold text-text-a0 text-xl">
                Permissions
              </h2>
              <p className="text-sm text-text-a30 leading-relaxed">
                Create and manage permissions. Only orphaned permissions (not
                assigned to any roles) can be deleted.
              </p>
            </div>
            <Button
              type="button"
              variant="primary"
              size="xsmall"
              onClick={permissionModal.openCreate}
              className="flex-shrink-0"
            >
              <i className="pi pi-plus" aria-hidden="true" />
              Add permission
            </Button>
          </div>
          <PermissionsTable
            permissions={permissions}
            isLoading={isLoadingPermissions}
            onEdit={permissionModal.openEdit}
            onDelete={permissionDeleteState.openDelete}
          />
        </div>
      </div>

      {userModal.isOpen && (
        <UserEditModal
          user={userModal.selectedItem}
          onClose={userModal.close}
          onSave={handleSaveUser}
        />
      )}

      {userDeleteState.isOpen && userDeleteState.itemToDelete && (
        <DeleteUserConfirmationModal
          isOpen={userDeleteState.isOpen}
          username={userDeleteState.itemToDelete.username}
          isDeleting={userDeleteState.isDeleting}
          error={userDeleteState.error}
          onClose={userDeleteState.close}
          onConfirm={handleConfirmDeleteUser}
        />
      )}

      {roleModal.isOpen && (
        <RoleEditModal
          role={roleModal.selectedItem}
          onClose={roleModal.close}
          onSave={handleSaveRole}
        />
      )}

      {roleDeleteState.isOpen && roleDeleteState.itemToDelete && (
        <DeleteRoleConfirmationModal
          isOpen={roleDeleteState.isOpen}
          roleName={roleDeleteState.itemToDelete.name}
          isDeleting={roleDeleteState.isDeleting}
          error={roleDeleteState.error}
          onClose={roleDeleteState.close}
          onConfirm={handleConfirmDeleteRole}
        />
      )}

      {showPermissionEditModal &&
        roleModal.selectedItem &&
        selectedRolePermission && (
          <PermissionEditModal
            permission={selectedRolePermission.permission}
            rolePermission={selectedRolePermission}
            role={roleModal.selectedItem}
            onClose={() => {
              setShowPermissionEditModal(false);
              roleModal.close();
              setSelectedRolePermission(null);
            }}
            onSave={(data) => {
              // In role context, data is always a Role
              handleSaveRolePermission(data as Role);
            }}
          />
        )}

      {permissionModal.isOpen && (
        <PermissionEditModal
          permission={permissionModal.selectedItem ?? null}
          onClose={permissionModal.close}
          onSave={handleSavePermission}
        />
      )}

      {permissionDeleteState.isOpen && permissionDeleteState.itemToDelete && (
        <DeletePermissionConfirmationModal
          isOpen={permissionDeleteState.isOpen}
          permissionName={permissionDeleteState.itemToDelete.name}
          isDeleting={permissionDeleteState.isDeleting}
          error={permissionDeleteState.error}
          onClose={permissionDeleteState.close}
          onConfirm={handleConfirmDeletePermission}
        />
      )}
    </>
  );
}
