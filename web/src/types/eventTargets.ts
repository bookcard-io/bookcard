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
 * Abstract event targets for DOM event subscription.
 *
 * Notes
 * -----
 * These interfaces allow hooks to depend on abstractions rather than concrete
 * globals like `window`/`document`, which improves testability (DIP).
 */

/**
 * Interface for event targets capable of keydown subscription.
 *
 * Notes
 * -----
 * This avoids hard dependencies on `window`/`document` and improves testability.
 */
export interface KeydownEventTarget {
  addEventListener: (
    type: "keydown",
    listener: (e: KeyboardEvent) => void,
    options?: AddEventListenerOptions | boolean,
  ) => void;
  removeEventListener: (
    type: "keydown",
    listener: (e: KeyboardEvent) => void,
    options?: EventListenerOptions | boolean,
  ) => void;
}
