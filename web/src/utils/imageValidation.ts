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
 * Image validation utilities.
 *
 * Provides constants and validation functions for image file handling.
 * Follows SRP by separating image validation logic from components.
 * Follows DRY by centralizing image validation constants.
 */

/**
 * Valid MIME types for image files.
 */
export const VALID_IMAGE_TYPES = [
  "image/jpeg",
  "image/jpg",
  "image/png",
  "image/gif",
  "image/webp",
  "image/svg+xml",
] as const;

/**
 * Maximum file size for image uploads (5MB in bytes).
 */
export const MAX_IMAGE_SIZE = 5 * 1024 * 1024;

/**
 * Accept attribute value for image file inputs.
 */
export const IMAGE_ACCEPT_ATTRIBUTE =
  "image/jpeg,image/jpg,image/png,image/gif,image/webp,image/svg+xml";

/**
 * Validate image file type.
 *
 * Parameters
 * ----------
 * file : File
 *     File to validate.
 *
 * Returns
 * -------
 * boolean
 *     True if file type is valid, false otherwise.
 */
export function isValidImageType(file: File): boolean {
  return VALID_IMAGE_TYPES.includes(
    file.type as (typeof VALID_IMAGE_TYPES)[number],
  );
}

/**
 * Validate image file size.
 *
 * Parameters
 * ----------
 * file : File
 *     File to validate.
 *
 * Returns
 * -------
 * boolean
 *     True if file size is within limit, false otherwise.
 */
export function isValidImageSize(file: File): boolean {
  return file.size <= MAX_IMAGE_SIZE;
}

/**
 * Validate image file (type and size).
 *
 * Parameters
 * ----------
 * file : File
 *     File to validate.
 *
 * Returns
 * -------
 * { valid: boolean; error?: string }
 *     Validation result with optional error message.
 */
export function validateImageFile(file: File): {
  valid: boolean;
  error?: string;
} {
  if (!isValidImageType(file)) {
    return {
      valid: false,
      error: "Invalid file type. Please select an image file.",
    };
  }

  if (!isValidImageSize(file)) {
    return {
      valid: false,
      error: "File size must be less than 5MB",
    };
  }

  return { valid: true };
}
