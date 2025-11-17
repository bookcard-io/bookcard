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

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/forms/Button";
import { PermissionMultiTextInput } from "@/components/forms/PermissionMultiTextInput";
import { TextArea } from "@/components/forms/TextArea";
import { TextInput } from "@/components/forms/TextInput";
import { useModal } from "@/hooks/useModal";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import { useRoleForm } from "@/hooks/useRoleForm";
import { useRolePermissions } from "@/hooks/useRolePermissions";
import { cn } from "@/libs/utils";
import type {
  Permission,
  Role,
  RoleCreate,
  RoleUpdate,
} from "@/services/roleService";
import { renderModalPortal } from "@/utils/modal";
import {
  buildPermissionAssignments,
  calculateRemovedPermissionIds,
} from "@/utils/rolePermissionAssignment";

export interface RoleEditModalProps {
  /** Role to edit (null for create mode). */
  role?: Role | null;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when role is saved. Returns the created/updated role. */
  onSave: (data: RoleCreate | RoleUpdate) => Promise<Role>;
  /** All available permissions for reference. */
  availablePermissions?: Permission[];
}

/**
 * Role create/edit modal component.
 *
 * Displays a form for creating or editing a role in a modal overlay.
 * Follows SRP by delegating concerns to specialized hooks.
 * Follows IOC by accepting callbacks for all operations.
 *
 * Parameters
 * ----------
 * props : RoleEditModalProps
 *     Component props including role, onClose, and onSave callbacks.
 */
export function RoleEditModal({
  role,
  onClose,
  onSave,
  availablePermissions = [],
}: RoleEditModalProps) {
  // Form state and validation (SRP via hook)
  const {
    formData,
    isSubmitting,
    errors,
    generalError,
    isLocked,
    isEditMode,
    setName,
    setDescription,
    clearFieldError,
    handleSubmit,
    reset: resetForm,
    setGeneralError,
  } = useRoleForm({
    role,
    onSubmit: onSave,
    onError: (error) => {
      console.error("Failed to save role:", error);
    },
  });

  // Permission management (SRP via hook)
  const {
    permissionNames,
    newPermissionDetails,
    conditionErrors,
    permissionMap,
    existingPermissionNames,
    newPermissionNames,
    setPermissionNames,
    removeExistingPermission,
    removeNewPermission,
    updateNewPermissionDetail,
    reset: resetPermissions,
  } = useRolePermissions({
    initialPermissionNames:
      role?.permissions.map((rp) => rp.permission.name) ?? [],
    availablePermissions,
  });

  // Info box dismissal state
  const [isInfoBoxDismissed, setIsInfoBoxDismissed] = useState(false);
  const previousRoleIdRef = useRef<number | null>(role?.id ?? null);

  // Reset info box dismissal when role changes
  useEffect(() => {
    const currentRoleId = role?.id ?? null;
    if (previousRoleIdRef.current !== currentRoleId) {
      setIsInfoBoxDismissed(false);
      previousRoleIdRef.current = currentRoleId;
    }
  }, [role?.id]);

  // Prevent body scroll when modal is open
  useModal(true);

  // Use standardized modal interaction handlers (DRY, SRP)
  const { handleOverlayClick, handleModalClick, handleOverlayKeyDown } =
    useModalInteractions({ onClose });

  // Check for condition JSON errors before submission
  const hasConditionErrors = Object.values(conditionErrors).some(
    (error) => error !== "",
  );

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Check for condition JSON errors
    if (hasConditionErrors) {
      setGeneralError("Please fix all condition JSON errors before saving");
      return;
    }

    try {
      // Build permission assignments (DRY via utility)
      const permissionAssignments = buildPermissionAssignments(
        existingPermissionNames,
        newPermissionNames,
        permissionMap,
        newPermissionDetails,
        role,
        isEditMode,
      );

      // Calculate removed permission IDs for update mode
      let removedPermissionIds: number[] | undefined;
      if (isEditMode && role) {
        removedPermissionIds = calculateRemovedPermissionIds(
          role,
          existingPermissionNames,
          permissionMap,
        );
      }

      // Submit form (handles create/update logic)
      const success = await handleSubmit(
        permissionAssignments,
        removedPermissionIds,
      );

      if (success) {
        onClose();
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to save role";
      setGeneralError(errorMessage);
    }
  };

  const handleCancel = () => {
    resetForm();
    resetPermissions();
    onClose();
  };

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
          "modal-container modal-container-shadow-default w-full max-w-6xl flex-col",
          "max-h-[90vh] min-h-[90vh] overflow-hidden",
        )}
        role="dialog"
        aria-modal="true"
        aria-label={isEditMode ? "Edit role" : "Create role"}
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
                {isEditMode ? "Edit role" : "Create role"}
              </h2>
              {isLocked && (
                <span
                  className={cn(
                    "inline-flex items-center gap-1 rounded-md bg-warning-a20 px-2 py-1 font-medium text-warning-a0 text-xs",
                  )}
                  title="This role is locked and cannot be deleted or have permissions removed"
                >
                  <i className={cn("pi pi-lock text-xs")} aria-hidden="true" />
                  Locked
                </span>
              )}
            </div>
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
            {/* Locked Role Info Box */}
            {isLocked && !isInfoBoxDismissed && (
              <div
                className={cn(
                  "relative flex items-start gap-3 rounded-md border border-info-a20 bg-info-a20 p-4",
                )}
              >
                <div className={cn("flex flex-1 flex-col gap-1")}>
                  <div className={cn("flex items-center gap-2")}>
                    <i
                      className={cn("pi pi-info-circle text-info-a0 text-sm")}
                      aria-hidden="true"
                    />
                    <span className={cn("font-medium text-info-a0 text-sm")}>
                      Role is Locked
                    </span>
                  </div>
                  <p className={cn("m-0 text-info-a0 text-sm leading-relaxed")}>
                    This role is locked. You may modify the description and add
                    new permissions, but you cannot change the name or remove
                    existing permissions.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setIsInfoBoxDismissed(true)}
                  className={cn(
                    "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-none bg-transparent p-0 text-info-a0 transition-colors hover:bg-info-a20/50",
                  )}
                  aria-label="Dismiss info box"
                >
                  <i className={cn("pi pi-times text-xs")} aria-hidden="true" />
                </button>
              </div>
            )}

            <div
              className={cn(
                "grid grid-cols-[minmax(0,25%)_minmax(0,1fr)] gap-4",
              )}
            >
              <TextInput
                id="name"
                label="Name"
                value={formData.name}
                onChange={(e) => {
                  setName(e.target.value);
                  clearFieldError("name");
                }}
                error={errors.name}
                required
                autoFocus
                disabled={isLocked}
              />
              <TextInput
                id="description"
                label="Description"
                value={formData.description}
                onChange={(e) => {
                  setDescription(e.target.value);
                  clearFieldError("description");
                }}
                error={errors.description}
                placeholder="Optional role description"
              />
            </div>

            {/* Permissions Section */}
            <div className={cn("flex flex-col gap-4")}>
              <div className={cn("flex flex-col gap-2")}>
                <h3 className={cn("m-0 font-semibold text-lg text-text-a0")}>
                  Permissions
                </h3>
                <p className={cn("m-0 text-sm text-text-a30")}>
                  Add or remove permissions for this role. New permissions will
                  be created if they don't exist.
                </p>
              </div>

              <PermissionMultiTextInput
                id="permissions"
                // label="Permission Names"
                values={permissionNames}
                onChange={setPermissionNames}
                placeholder="Type permission name and press Enter, e.g. `books:read`."
                //helperText="Enter permission names or select from suggestions"
              />

              {/* Existing Permissions */}
              {existingPermissionNames.length > 0 && (
                <div className={cn("flex flex-col gap-3")}>
                  <h4 className={cn("m-0 font-medium text-base text-text-a0")}>
                    Existing Permissions
                  </h4>
                  <div className={cn("flex flex-wrap gap-2")}>
                    {existingPermissionNames.map((permName) => {
                      const permission = permissionMap.get(permName);
                      return (
                        <div
                          key={permName}
                          className={cn(
                            "inline-flex items-center gap-2 rounded-md border border-surface-a20 bg-surface-tonal-a10 px-3 py-2",
                          )}
                        >
                          <div className={cn("flex flex-col gap-0.5")}>
                            <span
                              className={cn("font-medium text-sm text-text-a0")}
                            >
                              {permName}
                            </span>
                            {permission?.description && (
                              <span className={cn("text-text-a30 text-xs")}>
                                {permission.description}
                              </span>
                            )}
                            <span className={cn("text-text-a40 text-xs")}>
                              {permission?.resource}:{permission?.action}
                            </span>
                          </div>
                          {!isLocked && (
                            <button
                              type="button"
                              onClick={() => removeExistingPermission(permName)}
                              className={cn(
                                "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-none bg-transparent p-0 text-text-a30 transition-colors hover:bg-danger-a20 hover:text-danger-a0",
                              )}
                              aria-label={`Remove ${permName}`}
                            >
                              <i
                                className={cn("pi pi-times text-xs")}
                                aria-hidden="true"
                              />
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* New Permissions */}
              {newPermissionNames.length > 0 && (
                <div className={cn("flex flex-col gap-3")}>
                  <h4 className={cn("m-0 font-medium text-base text-text-a0")}>
                    New Permissions
                  </h4>
                  <p className={cn("m-0 text-sm text-text-a30")}>
                    These permissions don't exist yet. Provide details to create
                    them.
                  </p>
                  <div className={cn("flex flex-col gap-4")}>
                    {newPermissionNames.map((permName) => {
                      const details = newPermissionDetails[permName] || {
                        description: "",
                        resource: "",
                        action: "",
                        condition: "",
                      };
                      const conditionError = conditionErrors[permName] || "";
                      return (
                        <div
                          key={permName}
                          className={cn(
                            "flex flex-col gap-3 rounded-md border border-warning-a20 bg-surface-tonal-a10 p-4",
                          )}
                        >
                          <div
                            className={cn(
                              "flex items-center justify-between gap-2 border-surface-a20 border-b pb-2",
                            )}
                          >
                            <span
                              className={cn(
                                "font-medium text-sm text-warning-a0",
                              )}
                            >
                              {permName}
                            </span>
                            <button
                              type="button"
                              onClick={() => removeNewPermission(permName)}
                              className={cn(
                                "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-none bg-transparent p-0 text-text-a30 transition-colors hover:bg-danger-a20 hover:text-danger-a0",
                              )}
                              aria-label={`Remove ${permName}`}
                            >
                              <i
                                className={cn("pi pi-times text-xs")}
                                aria-hidden="true"
                              />
                            </button>
                          </div>
                          <div
                            className={cn(
                              "grid grid-cols-1 gap-3 md:grid-cols-2",
                            )}
                          >
                            <TextInput
                              id={`${permName}-resource`}
                              label="Resource"
                              value={details.resource}
                              onChange={(e) =>
                                updateNewPermissionDetail(
                                  permName,
                                  "resource",
                                  e.target.value,
                                )
                              }
                              placeholder="e.g., books, users"
                              required
                            />
                            <TextInput
                              id={`${permName}-action`}
                              label="Action"
                              value={details.action}
                              onChange={(e) =>
                                updateNewPermissionDetail(
                                  permName,
                                  "action",
                                  e.target.value,
                                )
                              }
                              placeholder="e.g., read, write, delete"
                              required
                            />
                          </div>
                          <TextInput
                            id={`${permName}-description`}
                            label="Description"
                            value={details.description}
                            onChange={(e) =>
                              updateNewPermissionDetail(
                                permName,
                                "description",
                                e.target.value,
                              )
                            }
                            placeholder="Optional description for this permission"
                          />
                          <TextArea
                            id={`${permName}-condition`}
                            label="Condition (JSON)"
                            value={details.condition}
                            onChange={(e) =>
                              updateNewPermissionDetail(
                                permName,
                                "condition",
                                e.target.value,
                              )
                            }
                            placeholder='Optional JSON condition, e.g., {"author": "Stephen King", "tags": ["Short Stories"]}'
                            error={conditionError}
                            helperText="Optional JSON object for conditional permissions"
                            rows={4}
                          />
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
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
              <Button
                type="button"
                variant="ghost"
                size="medium"
                onClick={handleCancel}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="medium"
                loading={isSubmitting}
              >
                {isEditMode ? "Save changes" : "Create role"}
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
