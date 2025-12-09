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
 * Result type for functional error handling.
 *
 * Follows functional programming patterns to avoid throwing exceptions
 * and make error handling explicit in the type system.
 */

export type Result<T, E = Error> = Ok<T> | Err<E>;

export class Ok<T> {
  readonly isOk = true;
  readonly isErr = false;

  constructor(public readonly value: T) {}

  /**
   * Map the value if this is an Ok result.
   *
   * Parameters
   * ----------
   * fn : (value: T) => U
   *     Function to transform the value.
   *
   * Returns
   * -------
   * Result<U, E>
   *     New Result with transformed value or same error.
   */
  map<U>(fn: (value: T) => U): Result<U, never> {
    return ok(fn(this.value));
  }

  /**
   * Match on the result, calling the appropriate handler.
   *
   * Parameters
   * ----------
   * handlers : { ok: (value: T) => U; err: (error: E) => U }
   *     Handlers for Ok and Err cases.
   *
   * Returns
   * -------
   * U
   *     Result of the ok handler.
   */
  match<E, U>(handlers: { ok: (value: T) => U; err: (error: E) => U }): U {
    return handlers.ok(this.value);
  }
}

export class Err<E> {
  readonly isOk = false;
  readonly isErr = true;

  constructor(public readonly error: E) {}

  /**
   * Map the value if this is an Ok result.
   *
   * Parameters
   * ----------
   * fn : (value: T) => U
   *     Function to transform the value (not called for Err).
   *
   * Returns
   * -------
   * Result<U, E>
   *     Same error result.
   */
  map<T, U>(_fn: (value: T) => U): Result<U, E> {
    return err(this.error);
  }

  /**
   * Match on the result, calling the appropriate handler.
   *
   * Parameters
   * ----------
   * handlers : { ok: (value: T) => U; err: (error: E) => U }
   *     Handlers for Ok and Err cases.
   *
   * Returns
   * -------
   * U
   *     Result of the err handler.
   */
  match<T, U>(handlers: { ok: (value: T) => U; err: (error: E) => U }): U {
    return handlers.err(this.error);
  }
}

/**
 * Create an Ok result.
 *
 * Parameters
 * ----------
 * value : T
 *     The success value.
 *
 * Returns
 * -------
 * Ok<T>
 *     An Ok result containing the value.
 */
export function ok<T>(value: T): Ok<T> {
  return new Ok(value);
}

/**
 * Create an Err result.
 *
 * Parameters
 * ----------
 * error : E
 *     The error value.
 *
 * Returns
 * -------
 * Err<E>
 *     An Err result containing the error.
 */
export function err<E>(error: E): Err<E> {
  return new Err(error);
}
