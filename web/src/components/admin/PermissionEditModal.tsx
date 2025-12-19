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
import { DeletePermissionConfirmationModal } from "@/components/admin/DeletePermissionConfirmationModal";
import { Button } from "@/components/forms/Button";
import { TextArea } from "@/components/forms/TextArea";
import { TextInput } from "@/components/forms/TextInput";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { useRoles } from "@/contexts/RolesContext";
import { useModal } from "@/hooks/useModal";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import { usePermissionDelete } from "@/hooks/usePermissionDelete";
import { usePermissionForm } from "@/hooks/usePermissionForm";
import { usePermissionRules } from "@/hooks/usePermissionRules";
import { usePermissionSubmit } from "@/hooks/usePermissionSubmit";
import { cn } from "@/libs/utils";
import type { Permission, Role, RolePermission } from "@/services/roleService";
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
 * Follows IOC by accepting callbacks for all operations and injecting services.
 * Follows DRY by consolidating both use cases into one component and reusing utilities.
 * Follows SOC by separating business logic, API calls, and presentation.
 */
export function PermissionEditModal({
  permission,
  rolePermission,
  role,
  onClose,
  onSave,
}: PermissionEditModalProps) {
  const { showDanger } = useGlobalMessages();
  const { updateRole: updateRoleOptimistic, roles, refresh } = useRoles();
  const isRoleContext = rolePermission !== undefined && role !== undefined;
  const isEditMode = permission != null;
  const isLocked = role?.locked ?? false;
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);

  // Use permission rules hook for business logic (SOC)
  const { isOrphaned } = usePermissionRules({
    roles,
    permission,
    isRoleContext,
  });

  // Prevent body scroll when modal is open
  useModal(true);

  // Use standardized modal interaction handlers (DRY, SRP)
  const { handleOverlayClick, handleModalClick, handleOverlayKeyDown } =
    useModalInteractions({ onClose });

  // Inject operations for IOC (services can be mocked for testing)
  const submitOperations = {
    createPermission,
    updatePermission,
    updateRolePermission,
    updateRoleOptimistic,
  };

  // Use permission submit hook for submission logic (SRP)
  const handleSubmit = usePermissionSubmit({
    isRoleContext,
    isEditMode,
    permission,
    rolePermission,
    role,
    operations: submitOperations,
    onSave: (data) => {
      onSave(data);
      onClose();
    },
    onCancel: onClose,
    onError: showDanger,
  });

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
    onSubmit: handleSubmit,
    onError: showDanger,
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

  // Inject operations for deletion (IOC)
  const deleteOperations = {
    deletePermission,
    refreshRoles: refresh,
  };

  // Use permission delete hook for deletion logic (SRP)
  const { isDeleting, deleteError, handleDelete } = usePermissionDelete({
    permission,
    isOrphaned: isOrphaned(),
    operations: deleteOperations,
    onSuccess: () => {
      setShowDeleteConfirmation(false);
      onClose();
    },
    onError: showDanger,
  });

  const handleDeleteClick = useCallback(() => {
    setShowDeleteConfirmation(true);
  }, []);

  const handleDeleteCancel = useCallback(() => {
    setShowDeleteConfirmation(false);
  }, []);

  // Compute modal title (fix conditional logic)
  const modalTitle =
    isEditMode || isRoleContext ? "Edit permission" : "Create permission";

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
        aria-label={modalTitle}
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
                {isRoleContext ? "Edit permission for role" : modalTitle}
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
            </div>
            <div className="flex w-full flex-shrink-0 flex-col-reverse justify-end gap-3 md:w-auto md:flex-row">
              {isRoleContext && isOrphaned() && (
                <Button
                  type="button"
                  variant="danger"
                  size="medium"
                  onClick={handleDeleteClick}
                  disabled={isSubmitting || isDeleting}
                >
                  Delete permission
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

  return (
    <>
      {/* Render modal in a portal to avoid DOM hierarchy conflicts (DRY via utility) */}
      {renderModalPortal(modalContent)}
      {/* Delete confirmation modal */}
      {permission && (
        <DeletePermissionConfirmationModal
          isOpen={showDeleteConfirmation}
          permissionName={permission.name}
          isDeleting={isDeleting}
          error={deleteError}
          onClose={handleDeleteCancel}
          onConfirm={handleDelete}
        />
      )}
    </>
  );
}
