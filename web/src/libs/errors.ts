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

import { NextResponse } from "next/server";
import type { Result } from "./result";
import { err } from "./result";

/**
 * Base error class for API errors.
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number = 500,
  ) {
    super(message);
    this.name = "ApiError";
  }

  /**
   * Convert error to NextResponse.
   *
   * Returns
   * -------
   * NextResponse
   *     JSON error response with appropriate status code.
   */
  toResponse(): NextResponse {
    return NextResponse.json(
      { detail: this.message },
      { status: this.statusCode },
    );
  }
}

/**
 * Validation error for invalid input.
 */
export class ValidationError extends ApiError {
  constructor(message: string) {
    super(message, 400);
    this.name = "ValidationError";
  }
}

/**
 * Authentication error.
 */
export class AuthenticationError extends ApiError {
  constructor(message: string = "Unauthorized") {
    super(message, 401);
    this.name = "AuthenticationError";
  }
}

/**
 * Not found error.
 */
export class NotFoundError extends ApiError {
  constructor(message: string = "Resource not found") {
    super(message, 404);
    this.name = "NotFoundError";
  }
}

/**
 * Unsupported content type error.
 */
export class UnsupportedContentTypeError extends ApiError {
  constructor(message: string = "Unsupported content type") {
    super(message, 415);
    this.name = "UnsupportedContentTypeError";
  }
}

/**
 * Create a Result from an error.
 *
 * Parameters
 * ----------
 * error : Error | string
 *     Error instance or error message.
 * statusCode : number
 *     HTTP status code (default: 500).
 *
 * Returns
 * -------
 * Result<never, ApiError>
 *     Err result containing the ApiError.
 */
export function errorResult(
  error: Error | string,
  statusCode: number = 500,
): Result<never, ApiError> {
  if (error instanceof ApiError) {
    return err(error);
  }
  if (error instanceof Error) {
    return err(new ApiError(error.message, statusCode));
  }
  return err(new ApiError(error, statusCode));
}
