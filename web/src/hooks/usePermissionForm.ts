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
import type { Permission, RolePermission } from "@/services/roleService";
import {
  type PermissionFormData,
  type PermissionValidationErrors,
  validateConditionJson,
  validatePermissionForm,
} from "@/utils/permissionValidation";

export interface UsePermissionFormOptions {
  /** Initial permission data. */
  permission?: Permission;
  /** Initial role permission data. */
  rolePermission?: RolePermission;
  /** Callback when form is successfully submitted. */
  onSubmit?: (data: PermissionFormData) => Promise<void>;
  /** Callback when form submission fails. */
  onError?: (error: string) => void;
}

export interface UsePermissionFormReturn {
  /** Current form values. */
  formData: PermissionFormData;
  /** Whether form is being submitted. */
  isSubmitting: boolean;
  /** Form validation errors. */
  errors: PermissionValidationErrors;
  /** General error message. */
  generalError: string | null;
  /** Update name value. */
  setName: (name: string) => void;
  /** Update description value. */
  setDescription: (description: string) => void;
  /** Update resource value. */
  setResource: (resource: string) => void;
  /** Update action value. */
  setAction: (action: string) => void;
  /** Update condition value. */
  setCondition: (condition: string) => void;
  /** Clear field error when user starts typing. */
  clearFieldError: (field: keyof PermissionValidationErrors) => void;
  /** Validate and submit the form. */
  handleSubmit: () => Promise<boolean>;
  /** Reset form to initial values. */
  reset: () => void;
  /** Validate the form. */
  validate: () => boolean;
}

/**
 * Hook for permission edit form logic.
 *
 * Manages form state, validation, and submission for permission editing.
 * Follows SRP by separating form logic from UI components.
 * Follows DRY by centralizing form state management.
 * Follows IOC by accepting callbacks as dependencies.
 *
 * Parameters
 * ----------
 * options : UsePermissionFormOptions
 *     Configuration options for the form.
 *
 * Returns
 * -------
 * UsePermissionFormReturn
 *     Object with form state and handlers.
 */
export function usePermissionForm(
  options: UsePermissionFormOptions,
): UsePermissionFormReturn {
  const { permission, rolePermission, onSubmit, onError } = options;

  const initialFormData = useMemo<PermissionFormData>(
    () => ({
      name: permission?.name || "",
      description: permission?.description || "",
      resource: permission?.resource || "",
      action: permission?.action || "",
      condition: rolePermission?.condition
        ? JSON.stringify(rolePermission.condition, null, 2)
        : "",
    }),
    [
      permission?.name,
      permission?.description,
      permission?.resource,
      permission?.action,
      rolePermission?.condition,
    ],
  );

  const [formData, setFormData] = useState<PermissionFormData>(initialFormData);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<PermissionValidationErrors>({});
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

  const setResource = useCallback(
    (resource: string) => {
      setFormData((prev) => ({ ...prev, resource }));
      if (errors.resource) {
        setErrors((prev) => ({ ...prev, resource: undefined }));
      }
    },
    [errors.resource],
  );

  const setAction = useCallback(
    (action: string) => {
      setFormData((prev) => ({ ...prev, action }));
      if (errors.action) {
        setErrors((prev) => ({ ...prev, action: undefined }));
      }
    },
    [errors.action],
  );

  const setCondition = useCallback((condition: string) => {
    setFormData((prev) => ({ ...prev, condition }));
    const error = validateConditionJson(condition);
    setErrors((prev) => ({
      ...prev,
      condition: error,
    }));
  }, []);

  const clearFieldError = useCallback(
    (field: keyof PermissionValidationErrors) => {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    },
    [],
  );

  const validate = useCallback((): boolean => {
    const validationErrors = validatePermissionForm(formData);
    setErrors(validationErrors);
    return Object.keys(validationErrors).length === 0;
  }, [formData]);

  const handleSubmit = useCallback(async (): Promise<boolean> => {
    setGeneralError(null);

    if (!validate()) {
      return false;
    }

    if (!onSubmit) {
      return false;
    }

    setIsSubmitting(true);

    try {
      await onSubmit(formData);
      return true;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to save permission";
      setGeneralError(errorMessage);
      onError?.(errorMessage);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }, [formData, validate, onSubmit, onError]);

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
    setName,
    setDescription,
    setResource,
    setAction,
    setCondition,
    clearFieldError,
    handleSubmit,
    reset,
    validate,
  };
}
