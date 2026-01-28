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
 * DOM event utilities.
 *
 * Notes
 * -----
 * These helpers keep UI behavior consistent and avoid duplicated checks
 * scattered throughout the codebase (DRY).
 */

/**
 * Check whether a keyboard event target should be treated as "editable".
 *
 * Parameters
 * ----------
 * target : EventTarget | null
 *     Event target to check.
 *
 * Returns
 * -------
 * bool
 *     True if the target is an input/textarea/select/contenteditable element.
 */
export function isEditableEventTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;

  if (target.isContentEditable) return true;

  switch (target.tagName) {
    case "INPUT":
    case "TEXTAREA":
    case "SELECT":
      return true;
    default:
      return false;
  }
}
