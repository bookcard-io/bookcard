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

import { ApiError } from "../errors";
import type { Result } from "../result";
import { err, ok } from "../result";

/**
 * Safely parse JSON from text.
 *
 * Parameters
 * ----------
 * text : string
 *     The text to parse.
 *
 * Returns
 * -------
 * T | null
 *     Parsed JSON object or null if parsing fails.
 */
function safeJsonParse<T>(text: string): T | null {
  try {
    return JSON.parse(text) as T;
  } catch {
    return null;
  }
}

/**
 * Parse JSON response from fetch Response.
 *
 * Parameters
 * ----------
 * response : Response
 *     The fetch Response object.
 * fallbackError : string
 *     Error message to use if response parsing fails.
 *
 * Returns
 * -------
 * Promise<Result<T, ApiError>>
 *     Parsed response data or error.
 */
export async function parseJsonResponse<T>(
  response: Response,
  fallbackError: string,
): Promise<Result<T, ApiError>> {
  const text = await response.text();

  if (!response.ok) {
    const errorData = safeJsonParse<{ detail?: string }>(text);
    return err(
      new ApiError(errorData?.detail || fallbackError, response.status),
    );
  }

  const data = safeJsonParse<T>(text);
  if (!data) {
    return err(new ApiError("Invalid response from server", 500));
  }

  return ok(data);
}

/**
 * Build FormData for import request.
 *
 * Parameters
 * ----------
 * file : File
 *     The file to import.
 * options : { importer: string; autoMatch: boolean }
 *     Import options.
 *
 * Returns
 * -------
 * FormData
 *     FormData ready for backend request.
 */
export function buildImportFormData(
  file: File,
  options: { importer: string; autoMatch: boolean },
): FormData {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("importer", options.importer);
  formData.append("auto_match", String(options.autoMatch));
  return formData;
}
