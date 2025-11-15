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

import { useCallback, useMemo, useState } from "react";
import type { Role, RoleCreate, RoleUpdate } from "@/services/roleService";
import {
  type RoleFormData,
  type RoleValidationErrors,
  validateRoleForm,
} from "@/utils/roleValidation";

export interface UseRoleFormOptions {
  /** Initial role data (for edit mode). */
  role?: Role | null;
  /** Callback when form is successfully submitted. */
  onSubmit?: (data: RoleCreate | RoleUpdate) => Promise<Role>;
  /** Callback when form submission fails. */
  onError?: (error: string) => void;
}

export interface UseRoleFormReturn {
  /** Current form values. */
  formData: RoleFormData;
  /** Whether form is being submitted. */
  isSubmitting: boolean;
  /** Form validation errors. */
  errors: RoleValidationErrors;
  /** General error message. */
  generalError: string | null;
  /** Whether role is locked. */
  isLocked: boolean;
  /** Whether in edit mode. */
  isEditMode: boolean;
  /** Update name value. */
  setName: (name: string) => void;
  /** Update description value. */
  setDescription: (description: string) => void;
  /** Clear field error when user starts typing. */
  clearFieldError: (field: keyof RoleValidationErrors) => void;
  /** Validate and submit the form. */
  handleSubmit: (
    permissionAssignments: Array<{
      permission_id?: number | null;
      permission_name?: string | null;
      resource?: string | null;
      action?: string | null;
      permission_description?: string | null;
      condition?: Record<string, unknown> | null;
    }>,
    removedPermissionIds?: number[],
  ) => Promise<boolean>;
  /** Reset form to initial values. */
  reset: () => void;
  /** Validate the form. */
  validate: () => boolean;
  /** Set general error. */
  setGeneralError: (error: string | null) => void;
}

/**
 * Hook for role create/edit form logic.
 *
 * Manages form state, validation, and submission for role creation and editing.
 * Follows SRP by separating form logic from UI components.
 * Follows DRY by centralizing form state management.
 * Follows IOC by accepting callbacks as dependencies.
 *
 * Parameters
 * ----------
 * options : UseRoleFormOptions
 *     Configuration options for the form.
 *
 * Returns
 * -------
 * UseRoleFormReturn
 *     Object with form state and handlers.
 */
export function useRoleForm(options: UseRoleFormOptions): UseRoleFormReturn {
  const { role, onSubmit, onError } = options;

  const isEditMode = role !== null && role !== undefined;
  const isLocked = role?.locked ?? false;

  const initialFormData = useMemo<RoleFormData>(
    () => ({
      name: role?.name ?? "",
      description: role?.description ?? "",
    }),
    [role?.name, role?.description],
  );

  const [formData, setFormData] = useState<RoleFormData>(initialFormData);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<RoleValidationErrors>({});
  const [generalError, setGeneralError] = useState<string | null>(null);

  const setName = useCallback(
    (name: string) => {
      setFormData((prev) => ({ ...prev, name }));
      if (errors.name) {
        setErrors((prev) => ({ ...prev, name: undefined }));
      }
    },
    [errors.name],
  );

  const setDescription = useCallback(
    (description: string) => {
      setFormData((prev) => ({ ...prev, description }));
      if (errors.description) {
        setErrors((prev) => ({ ...prev, description: undefined }));
      }
    },
    [errors.description],
  );

  const clearFieldError = useCallback((field: keyof RoleValidationErrors) => {
    setErrors((prev) => ({ ...prev, [field]: undefined }));
  }, []);

  const validate = useCallback((): boolean => {
    const validationErrors = validateRoleForm(formData);
    setErrors(validationErrors);
    return Object.keys(validationErrors).length === 0;
  }, [formData]);

  const handleSubmit = useCallback(
    async (
      permissionAssignments: Array<{
        permission_id?: number | null;
        permission_name?: string | null;
        resource?: string | null;
        action?: string | null;
        permission_description?: string | null;
        condition?: Record<string, unknown> | null;
      }>,
      removedPermissionIds?: number[],
    ): Promise<boolean> => {
      setGeneralError(null);

      if (!validate()) {
        return false;
      }

      if (!onSubmit) {
        return false;
      }

      setIsSubmitting(true);

      try {
        if (isEditMode && role) {
          const data: RoleUpdate = {
            name: isLocked ? undefined : formData.name.trim(),
            description: formData.description.trim() || null,
            permissions:
              permissionAssignments.length > 0
                ? permissionAssignments
                : undefined,
            removed_permission_ids:
              removedPermissionIds && removedPermissionIds.length > 0
                ? removedPermissionIds
                : undefined,
          };
          await onSubmit(data);
        } else {
          const data: RoleCreate = {
            name: formData.name.trim(),
            description: formData.description.trim() || null,
            permissions:
              permissionAssignments.length > 0
                ? permissionAssignments
                : undefined,
          };
          await onSubmit(data);
        }
        return true;
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Failed to save role";
        setGeneralError(errorMessage);
        onError?.(errorMessage);
        return false;
      } finally {
        setIsSubmitting(false);
      }
    },
    [formData, validate, onSubmit, onError, isEditMode, role, isLocked],
  );

  const reset = useCallback(() => {
    setFormData(initialFormData);
    setErrors({});
    setGeneralError(null);
  }, [initialFormData]);

  return {
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
    reset,
    validate,
    setGeneralError,
  };
}
