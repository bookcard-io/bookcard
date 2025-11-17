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

import { useCallback, useState } from "react";
import { Button } from "@/components/forms/Button";
import { TextArea } from "@/components/forms/TextArea";
import { TextInput } from "@/components/forms/TextInput";
import { useRoles } from "@/contexts/RolesContext";
import { useModal } from "@/hooks/useModal";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import { usePermissionForm } from "@/hooks/usePermissionForm";
import { cn } from "@/libs/utils";
import type {
  Permission,
  PermissionUpdate,
  Role,
  RolePermission,
  RolePermissionUpdate,
} from "@/services/roleService";
import {
  createPermission,
  deletePermission,
  updatePermission,
  updateRolePermission,
} from "@/services/roleService";
import { renderModalPortal } from "@/utils/modal";

export interface PermissionEditModalProps {
  /** Permission to edit (null for create mode in standalone mode). */
  permission?: Permission | null;
  /** Role-permission association (if editing in role context). */
  rolePermission?: RolePermission;
  /** Role that owns this permission (if editing in role context). */
  role?: Role;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when permission is saved. Returns the created/updated permission (standalone) or updated role (role context). */
  onSave: (data: Permission | Role) => void;
}

/**
 * Permission edit modal component.
 *
 * Displays a form for creating or editing a permission.
 * Can operate in two modes:
 * - Standalone mode: Create/edit permissions independently (permission only)
 * - Role context mode: Edit permissions within a role context (permission + role-permission condition)
 *
 * Follows SRP by delegating concerns to specialized hooks.
 * Follows IOC by accepting callbacks for all operations.
 * Follows DRY by consolidating both use cases into one component.
 */
export function PermissionEditModal({
  permission,
  rolePermission,
  role,
  onClose,
  onSave,
}: PermissionEditModalProps) {
  const { updateRole: updateRoleOptimistic, roles, refresh } = useRoles();
  const isRoleContext = rolePermission !== undefined && role !== undefined;
  const isEditMode = permission !== null && permission !== undefined;
  const isLocked = role?.locked ?? false;
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Check if permission is orphaned (only associated with this role)
  const isOrphaned = useCallback(() => {
    if (!isRoleContext || !permission) {
      return false;
    }
    // Count how many roles have this permission
    const roleCount = roles.filter((r) =>
      r.permissions.some((rp) => rp.permission.id === permission.id),
    ).length;
    // Orphaned if only associated with this one role
    return roleCount === 1;
  }, [isRoleContext, permission, roles]);

  // Prevent body scroll when modal is open
  useModal(true);

  // Use standardized modal interaction handlers (DRY, SRP)
  const { handleOverlayClick, handleModalClick, handleOverlayKeyDown } =
    useModalInteractions({ onClose });

  // Use permission form hook for form state and validation (SRP, DRY)
  const {
    formData,
    isSubmitting,
    errors,
    generalError,
    setName,
    setDescription,
    setResource,
    setAction,
    setCondition,
    handleSubmit: handleFormSubmitHook,
    reset,
  } = usePermissionForm({
    permission: permission ?? undefined,
    rolePermission: rolePermission ?? undefined,
    onSubmit: async (data) => {
      if (isRoleContext && rolePermission && role && permission) {
        // Role context mode: update permission and role-permission condition
        // Parse condition JSON if provided
        let conditionObj: Record<string, unknown> | null = null;
        if (data.condition.trim()) {
          conditionObj = JSON.parse(data.condition.trim());
        }

        // Update permission details
        const permissionUpdate: PermissionUpdate = {
          name:
            data.name.trim() !== permission.name ? data.name.trim() : undefined,
          description:
            data.description.trim() !== (permission.description ?? "")
              ? data.description.trim() || null
              : undefined,
          resource:
            data.resource.trim() !== permission.resource
              ? data.resource.trim()
              : undefined,
          action:
            data.action.trim() !== permission.action
              ? data.action.trim()
              : undefined,
        };

        // Only update permission if any field changed
        const hasPermissionChanges = Object.values(permissionUpdate).some(
          (v) => v !== undefined,
        );

        // Update role-permission condition
        const currentCondition = rolePermission.condition
          ? JSON.stringify(rolePermission.condition, null, 2)
          : "";
        const conditionChanged = data.condition.trim() !== currentCondition;

        if (conditionChanged) {
          // Update condition (this returns the full updated role)
          const rolePermissionUpdate: RolePermissionUpdate = {
            condition: conditionObj,
          };
          const updatedRole = await updateRolePermission(
            role.id,
            rolePermission.id,
            rolePermissionUpdate,
          );
          // If permission details also changed, update them first
          if (hasPermissionChanges) {
            await updatePermission(permission.id, permissionUpdate);
            // The role returned from updateRolePermission may not have the latest permission data
            // So we update it optimistically with the permission changes
            const roleWithUpdatedPermission: Role = {
              ...updatedRole,
              permissions: updatedRole.permissions.map((rp) =>
                rp.id === rolePermission.id
                  ? {
                      ...rp,
                      permission: {
                        ...rp.permission,
                        name: permissionUpdate.name ?? rp.permission.name,
                        description:
                          permissionUpdate.description !== undefined
                            ? permissionUpdate.description
                            : rp.permission.description,
                        resource:
                          permissionUpdate.resource ?? rp.permission.resource,
                        action: permissionUpdate.action ?? rp.permission.action,
                      },
                    }
                  : rp,
              ),
            };
            updateRoleOptimistic(roleWithUpdatedPermission);
            onSave(roleWithUpdatedPermission);
          } else {
            // Only condition changed
            updateRoleOptimistic(updatedRole);
            onSave(updatedRole);
          }
        } else if (hasPermissionChanges) {
          // Only permission details changed, update permission and construct updated role
          await updatePermission(permission.id, permissionUpdate);
          const updatedRole: Role = {
            ...role,
            permissions: role.permissions.map((rp) =>
              rp.id === rolePermission.id
                ? {
                    ...rp,
                    permission: {
                      ...rp.permission,
                      name: permissionUpdate.name ?? rp.permission.name,
                      description:
                        permissionUpdate.description !== undefined
                          ? permissionUpdate.description
                          : rp.permission.description,
                      resource:
                        permissionUpdate.resource ?? rp.permission.resource,
                      action: permissionUpdate.action ?? rp.permission.action,
                    },
                  }
                : rp,
            ),
          };
          updateRoleOptimistic(updatedRole);
          onSave(updatedRole);
        } else {
          // No changes
          onClose();
          return;
        }
      } else {
        // Standalone mode: create or update permission
        if (isEditMode && permission) {
          // Update existing permission
          const permissionUpdate: PermissionUpdate = {
            name:
              data.name.trim() !== permission.name
                ? data.name.trim()
                : undefined,
            description:
              data.description.trim() !== (permission.description ?? "")
                ? data.description.trim() || null
                : undefined,
            resource:
              data.resource.trim() !== permission.resource
                ? data.resource.trim()
                : undefined,
            action:
              data.action.trim() !== permission.action
                ? data.action.trim()
                : undefined,
          };

          // Only update if any field changed
          const hasChanges = Object.values(permissionUpdate).some(
            (v) => v !== undefined,
          );

          if (hasChanges) {
            const updatedPermission = await updatePermission(
              permission.id,
              permissionUpdate,
            );
            onSave(updatedPermission);
          } else {
            // No changes
            onClose();
            return;
          }
        } else {
          // Create new permission
          // Note: condition is not part of Permission, it's part of RolePermission
          // So we don't send condition when creating a standalone permission
          const newPermission = await createPermission({
            name: data.name.trim(),
            description: data.description.trim() || null,
            resource: data.resource.trim(),
            action: data.action.trim(),
          });
          onSave(newPermission);
        }
      }

      onClose();
    },
    onError: (error) => {
      console.error("Failed to save permission:", error);
    },
  });

  const handleFormSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      await handleFormSubmitHook();
    },
    [handleFormSubmitHook],
  );

  const handleCancel = useCallback(() => {
    reset();
    onClose();
  }, [reset, onClose]);

  const handleDeletePermission = useCallback(async () => {
    if (!isRoleContext || !permission) {
      return;
    }

    if (!isOrphaned()) {
      setDeleteError(
        "Cannot delete permission. This permission is associated with multiple roles. Please remove it from all roles first.",
      );
      return;
    }

    if (
      !confirm(
        `Are you sure you want to delete the permission "${permission.name}"? This action cannot be undone.`,
      )
    ) {
      return;
    }

    setIsDeleting(true);
    setDeleteError(null);

    try {
      await deletePermission(permission.id);
      // Refresh roles to ensure consistency
      await refresh();
      // Close modal
      onClose();
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to delete permission";
      setDeleteError(errorMessage);
    } finally {
      setIsDeleting(false);
    }
  }, [isRoleContext, isOrphaned, permission, onClose, refresh]);

  const modalContent = (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="modal-overlay modal-overlay-z-1002 modal-overlay-padding"
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
    >
      <div
        className={cn(
          "modal-container modal-container-shadow-default w-full max-w-4xl flex-col",
          "max-h-[90vh] overflow-hidden",
        )}
        role="dialog"
        aria-modal="true"
        aria-label={
          isRoleContext
            ? "Edit permission"
            : isEditMode
              ? "Edit permission"
              : "Create permission"
        }
        onMouseDown={handleModalClick}
      >
        <button
          type="button"
          onClick={onClose}
          className="modal-close-button modal-close-button-sm focus:outline"
          aria-label="Close"
        >
          <i className="pi pi-times" aria-hidden="true" />
        </button>

        <div className="flex items-start justify-between gap-4 border-surface-a20 border-b pt-6 pr-16 pb-4 pl-6">
          <div className="flex min-w-0 flex-1 flex-col gap-1">
            <div className={cn("flex items-center gap-2")}>
              <h2 className="m-0 truncate font-bold text-2xl text-text-a0 leading-[1.4]">
                {isRoleContext
                  ? "Edit Permission"
                  : isEditMode
                    ? "Edit permission"
                    : "Create permission"}
              </h2>
              {isLocked && (
                <span
                  className={cn(
                    "inline-flex items-center gap-1 rounded-md bg-warning-a20 px-2 py-1 font-medium text-warning-a0 text-xs",
                  )}
                  title="This role is locked"
                >
                  <i className={cn("pi pi-lock text-xs")} aria-hidden="true" />
                  Locked
                </span>
              )}
            </div>
            {isRoleContext && role && (
              <p className={cn("m-0 text-sm text-text-a30")}>
                Editing permission for role <strong>{role.name}</strong>
              </p>
            )}
          </div>
        </div>

        <form
          onSubmit={handleFormSubmit}
          className={cn("flex min-h-0 flex-1 flex-col overflow-hidden")}
        >
          <div
            className={cn(
              "flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto p-6",
            )}
          >
            <div className={cn("grid grid-cols-1 gap-4 md:grid-cols-2")}>
              <TextInput
                id="name"
                label="Name"
                value={formData.name}
                onChange={(e) => setName(e.target.value)}
                error={errors.name}
                required
                autoFocus
              />
              <TextInput
                id="description"
                label="Description"
                value={formData.description}
                onChange={(e) => setDescription(e.target.value)}
                error={errors.description}
                placeholder="Optional permission description"
              />
            </div>

            <div className={cn("grid grid-cols-1 gap-4 md:grid-cols-2")}>
              <TextInput
                id="resource"
                label="Resource"
                value={formData.resource}
                onChange={(e) => setResource(e.target.value)}
                error={errors.resource}
                placeholder="e.g., books, users"
                required
              />
              <TextInput
                id="action"
                label="Action"
                value={formData.action}
                onChange={(e) => setAction(e.target.value)}
                error={errors.action}
                placeholder="e.g., read, write, delete"
                required
              />
            </div>

            {/* Only show condition field in role context mode */}
            {isRoleContext && (
              <TextArea
                id="condition"
                label="Condition (JSON)"
                value={formData.condition}
                onChange={(e) => setCondition(e.target.value)}
                placeholder='Optional JSON condition, e.g., {"author": "Stephen King", "tags": ["Short Stories"]}'
                error={errors.condition}
                helperText="Optional JSON object for conditional permissions"
                rows={6}
              />
            )}
          </div>

          <div className={cn("modal-footer-between flex-shrink-0")}>
            <div className="flex w-full flex-1 flex-col gap-2">
              {generalError && (
                <p className="m-0 text-[var(--color-danger-a0)] text-sm">
                  {generalError}
                </p>
              )}
              {deleteError && (
                <p className="m-0 text-[var(--color-danger-a0)] text-sm">
                  {deleteError}
                </p>
              )}
            </div>
            <div className="flex w-full flex-shrink-0 flex-col-reverse justify-end gap-3 md:w-auto md:flex-row">
              {isRoleContext && isOrphaned() && (
                <Button
                  type="button"
                  variant="danger"
                  size="medium"
                  onClick={handleDeletePermission}
                  disabled={isSubmitting || isDeleting}
                  loading={isDeleting}
                >
                  Delete Permission
                </Button>
              )}
              <Button
                type="button"
                variant="ghost"
                size="medium"
                onClick={handleCancel}
                disabled={isSubmitting || isDeleting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="medium"
                loading={isSubmitting}
                disabled={isDeleting}
              >
                {isRoleContext
                  ? "Save changes"
                  : isEditMode
                    ? "Save changes"
                    : "Create permission"}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );

  // Render modal in a portal to avoid DOM hierarchy conflicts (DRY via utility)
  return renderModalPortal(modalContent);
}
