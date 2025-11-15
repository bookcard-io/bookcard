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
 * Permission validation utilities.
 *
 * Provides reusable validation functions for permission form inputs.
 * Follows SRP by separating validation logic from components.
 * Follows DRY by centralizing permission validation patterns.
 */

export interface PermissionValidationErrors {
  name?: string;
  description?: string;
  resource?: string;
  action?: string;
  condition?: string;
}

export interface PermissionFormData {
  name: string;
  description: string;
  resource: string;
  action: string;
  condition: string;
}

/**
 * Validate permission name.
 *
 * Parameters
 * ----------
 * name : string
 *     Permission name to validate.
 *
 * Returns
 * -------
 * string | undefined
 *     Error message if validation fails, undefined if valid.
 */
export function validatePermissionName(name: string): string | undefined {
  const trimmed = name.trim();
  if (!trimmed) {
    return "Name is required";
  }
  if (trimmed.length < 1) {
    return "Name must be at least 1 character";
  }
  if (trimmed.length > 100) {
    return "Name must be at most 100 characters";
  }
  return undefined;
}

/**
 * Validate permission description.
 *
 * Parameters
 * ----------
 * description : string
 *     Permission description to validate.
 *
 * Returns
 * -------
 * string | undefined
 *     Error message if validation fails, undefined if valid.
 */
export function validatePermissionDescription(
  description: string,
): string | undefined {
  if (description.length > 255) {
    return "Description must be at most 255 characters";
  }
  return undefined;
}

/**
 * Validate permission resource.
 *
 * Parameters
 * ----------
 * resource : string
 *     Permission resource to validate.
 *
 * Returns
 * -------
 * string | undefined
 *     Error message if validation fails, undefined if valid.
 */
export function validatePermissionResource(
  resource: string,
): string | undefined {
  const trimmed = resource.trim();
  if (!trimmed) {
    return "Resource is required";
  }
  if (trimmed.length < 1) {
    return "Resource must be at least 1 character";
  }
  if (trimmed.length > 50) {
    return "Resource must be at most 50 characters";
  }
  return undefined;
}

/**
 * Validate permission action.
 *
 * Parameters
 * ----------
 * action : string
 *     Permission action to validate.
 *
 * Returns
 * -------
 * string | undefined
 *     Error message if validation fails, undefined if valid.
 */
export function validatePermissionAction(action: string): string | undefined {
  const trimmed = action.trim();
  if (!trimmed) {
    return "Action is required";
  }
  if (trimmed.length < 1) {
    return "Action must be at least 1 character";
  }
  if (trimmed.length > 50) {
    return "Action must be at most 50 characters";
  }
  return undefined;
}

/**
 * Validate condition JSON string.
 *
 * Parameters
 * ----------
 * jsonString : string
 *     JSON string to validate.
 *
 * Returns
 * -------
 * string | undefined
 *     Error message if validation fails, undefined if valid.
 */
export function validateConditionJson(jsonString: string): string | undefined {
  if (!jsonString.trim()) {
    return undefined; // Empty is valid (optional field)
  }
  try {
    JSON.parse(jsonString);
    return undefined;
  } catch (error) {
    return error instanceof Error
      ? `Invalid JSON: ${error.message}`
      : "Invalid JSON format";
  }
}

/**
 * Validate all permission form fields.
 *
 * Parameters
 * ----------
 * data : PermissionFormData
 *     Form data to validate.
 *
 * Returns
 * -------
 * PermissionValidationErrors
 *     Object containing validation errors for each field.
 */
export function validatePermissionForm(
  data: PermissionFormData,
): PermissionValidationErrors {
  const errors: PermissionValidationErrors = {};

  const nameError = validatePermissionName(data.name);
  if (nameError) {
    errors.name = nameError;
  }

  const descriptionError = validatePermissionDescription(data.description);
  if (descriptionError) {
    errors.description = descriptionError;
  }

  const resourceError = validatePermissionResource(data.resource);
  if (resourceError) {
    errors.resource = resourceError;
  }

  const actionError = validatePermissionAction(data.action);
  if (actionError) {
    errors.action = actionError;
  }

  const conditionError = validateConditionJson(data.condition);
  if (conditionError) {
    errors.condition = conditionError;
  }

  return errors;
}
