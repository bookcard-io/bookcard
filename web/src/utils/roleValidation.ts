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
 * Role validation utilities.
 *
 * Provides reusable validation functions for role form inputs.
 * Follows SRP by separating validation logic from components.
 * Follows DRY by centralizing role validation patterns.
 */

export interface RoleValidationErrors {
  name?: string;
  description?: string;
}

export interface RoleFormData {
  name: string;
  description: string;
}

/**
 * Validate role name.
 *
 * Parameters
 * ----------
 * name : string
 *     Role name to validate.
 *
 * Returns
 * -------
 * string | undefined
 *     Error message if validation fails, undefined if valid.
 */
export function validateRoleName(name: string): string | undefined {
  const trimmed = name.trim();
  if (!trimmed) {
    return "Name is required";
  }
  if (trimmed.length < 1) {
    return "Name must be at least 1 character";
  }
  if (trimmed.length > 64) {
    return "Name must be at most 64 characters";
  }
  return undefined;
}

/**
 * Validate role description.
 *
 * Parameters
 * ----------
 * description : string
 *     Role description to validate.
 *
 * Returns
 * -------
 * string | undefined
 *     Error message if validation fails, undefined if valid.
 */
export function validateRoleDescription(
  description: string,
): string | undefined {
  if (description.length > 255) {
    return "Description must be at most 255 characters";
  }
  return undefined;
}

/**
 * Validate all role form fields.
 *
 * Parameters
 * ----------
 * data : RoleFormData
 *     Form data to validate.
 *
 * Returns
 * -------
 * RoleValidationErrors
 *     Object containing validation errors for each field.
 */
export function validateRoleForm(data: RoleFormData): RoleValidationErrors {
  const errors: RoleValidationErrors = {};

  const nameError = validateRoleName(data.name);
  if (nameError) {
    errors.name = nameError;
  }

  const descriptionError = validateRoleDescription(data.description);
  if (descriptionError) {
    errors.description = descriptionError;
  }

  return errors;
}
