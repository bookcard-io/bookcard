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

import type { ReadStatusValue } from "@/types/reading";

/**
 * Read status constants.
 */
export const READ_STATUSES = {
  READ: "read",
  NOT_READ: "not_read",
  READING: "reading",
} as const;

/**
 * Check if a read status indicates the book is read.
 *
 * Parameters
 * ----------
 * status : ReadStatusValue | null | undefined
 *     Read status value to check.
 *
 * Returns
 * -------
 * boolean
 *     True if the status is "read", false otherwise.
 */
export function isReadStatus(
  status: ReadStatusValue | null | undefined,
): boolean {
  return status === READ_STATUSES.READ;
}

/**
 * Check if a read status indicates the book is unread.
 *
 * Parameters
 * ----------
 * status : ReadStatusValue | null | undefined
 *     Read status value to check.
 *
 * Returns
 * -------
 * boolean
 *     True if the status is null, undefined, or "not_read", false otherwise.
 */
export function isUnreadStatus(
  status: ReadStatusValue | null | undefined,
): boolean {
  return status == null || status === READ_STATUSES.NOT_READ;
}
