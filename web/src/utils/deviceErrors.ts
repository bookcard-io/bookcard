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
 * Device error translation utilities.
 *
 * Translates technical error codes to user-friendly messages.
 * Follows SRP by separating error translation logic from components.
 * Follows DRY by centralizing error message mappings.
 */

/**
 * Device error code constants.
 */
export const DeviceErrorCode = {
  EMAIL_ALREADY_EXISTS: "device_email_already_exists",
} as const;

/**
 * Error code to user-friendly message mapping.
 */
const ERROR_MESSAGES: Record<string, string> = {
  [DeviceErrorCode.EMAIL_ALREADY_EXISTS]:
    "A device with this email already exists.",
};

/**
 * Translate device error code to user-friendly message.
 *
 * Parameters
 * ----------
 * errorCode : string
 *     Technical error code from the API.
 *
 * Returns
 * -------
 * string
 *     User-friendly error message.
 */
export function translateDeviceError(errorCode: string): string {
  return ERROR_MESSAGES[errorCode] || errorCode;
}

/**
 * Check if error is email-related.
 *
 * Parameters
 * ----------
 * errorCode : string
 *     Technical error code from the API.
 *
 * Returns
 * -------
 * boolean
 *     True if error is email-related, false otherwise.
 */
export function isEmailError(errorCode: string): boolean {
  return errorCode.includes("email") || errorCode.includes("device_email");
}
