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
 * Result returned by the probe-image API route.
 */
export interface ImageProbeResult {
  size: number | null;
  mimeType: string | null;
  extension: string | null;
}

/**
 * Configuration for probing remote images.
 */
export interface ImageProbeConfig {
  maxSizeBytes: number;
  timeoutMs: number;
  allowedSchemes: ReadonlySet<"http" | "https">;
  userAgent: string;
  followRedirects: boolean;
}

/**
 * Base error type for image probe failures with an HTTP status code.
 */
export class ImageProbeError extends Error {
  public readonly statusCode: number;

  /**
   * Parameters
   * ----------
   * message : string
   *     Error message safe to return to clients.
   * statusCode : number
   *     HTTP status code to return.
   * cause : unknown, optional
   *     Underlying error, if any.
   */
  constructor(message: string, statusCode: number, cause?: unknown) {
    super(message, cause !== undefined ? { cause } : undefined);
    this.name = "ImageProbeError";
    this.statusCode = statusCode;
  }
}

export class InvalidUrlError extends ImageProbeError {
  constructor(message = "Invalid URL", cause?: unknown) {
    super(message, 400, cause);
    this.name = "InvalidUrlError";
  }
}

export class SSRFError extends ImageProbeError {
  constructor(message = "Forbidden URL") {
    super(message, 400);
    this.name = "SSRFError";
  }
}

export class UpstreamError extends ImageProbeError {
  constructor(message: string, statusCode: number, cause?: unknown) {
    super(message, statusCode, cause);
    this.name = "UpstreamError";
  }
}

export class NotImageError extends ImageProbeError {
  constructor(message = "URL does not point to an image") {
    super(message, 400);
    this.name = "NotImageError";
  }
}

export class TooLargeError extends ImageProbeError {
  constructor(message = "Image too large") {
    super(message, 413);
    this.name = "TooLargeError";
  }
}
