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
 * No-op function that does nothing.
 *
 * Useful as a default callback to avoid null checks.
 */
export const noop = () => {};

/**
 * Provide a default no-op callback if the given callback is undefined.
 *
 * Follows DRY by eliminating repetitive `|| (() => {})` patterns.
 * Follows type safety by preserving callback signature.
 *
 * Parameters
 * ----------
 * fn : T | undefined
 *     Optional callback function.
 *
 * Returns
 * -------
 * T
 *     The provided callback or a no-op function with the same signature.
 *
 * Example
 * -------
 * ```ts
 * const handler = withDefault(onChange);
 * handler(value);  // Safe to call even if onChange was undefined
 * ```
 */
// biome-ignore lint/suspicious/noExplicitAny: This utility function needs to accept any function signature
export function withDefault<T extends (...args: any[]) => void>(
  fn: T | undefined,
): T {
  return (fn ?? noop) as T;
}
