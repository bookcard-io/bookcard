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
 * Validation utilities.
 *
 * Provides reusable validation functions for form inputs.
 * Follows SRP by separating validation logic from components.
 * Follows DRY by centralizing validation patterns.
 */

/**
 * Email validation regex pattern.
 */
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Validate email address format.
 *
 * Parameters
 * ----------
 * email : string
 *     Email address to validate.
 *
 * Returns
 * -------
 * boolean
 *     True if email format is valid, false otherwise.
 */
export function isValidEmail(email: string): boolean {
  return EMAIL_REGEX.test(email.trim());
}

/**
 * Validate email address and return error message if invalid.
 *
 * Parameters
 * ----------
 * email : string
 *     Email address to validate.
 *
 * Returns
 * -------
 * string | undefined
 *     Error message if validation fails, undefined if valid.
 */
export function validateEmail(email: string): string | undefined {
  const trimmed = email.trim();
  if (!trimmed) {
    return "Email is required.";
  }
  if (!isValidEmail(trimmed)) {
    return "Please enter a valid email address.";
  }
  return undefined;
}
