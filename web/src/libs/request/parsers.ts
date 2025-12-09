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

import type { ShelfCreate } from "@/types/shelf";
import { ValidationError } from "../errors";
import type { Result } from "../result";
import { err, ok } from "../result";

/**
 * Options for importing a read list.
 */
export interface ImportOptions {
  /** Importer name (e.g., "comicrack"). */
  importer: string;
  /** Whether to automatically match books. */
  autoMatch: boolean;
}

/**
 * Parsed import form data.
 */
export interface ImportFormData {
  /** The file to import. */
  file: File;
  /** Import options. */
  options: ImportOptions;
}

/**
 * Parsed shelf creation form data (multipart).
 */
export interface ShelfCreationFormData {
  /** Shelf creation data. */
  shelf: ShelfCreate;
  /** Optional file to import. */
  file: File | null;
  /** Import options (only used if file is provided). */
  importOptions: ImportOptions;
}

/**
 * Parse boolean field from FormData.
 *
 * Parameters
 * ----------
 * value : FormDataEntryValue | null
 *     The form data value.
 *
 * Returns
 * -------
 * boolean
 *     True if value is "true", "1", or "on", false otherwise.
 */
function parseBooleanField(value: FormDataEntryValue | null): boolean {
  return value === "true" || value === "1" || value === "on";
}

/**
 * Parse import form data from FormData.
 *
 * Parameters
 * ----------
 * formData : FormData
 *     The form data to parse.
 *
 * Returns
 * -------
 * Result<ImportFormData, ValidationError>
 *     Parsed import form data or validation error.
 */
export function parseImportFormData(
  formData: FormData,
): Result<ImportFormData, ValidationError> {
  const file = formData.get("file") as File | null;

  if (!file) {
    return err(new ValidationError("No file provided"));
  }

  const importer = (formData.get("importer") as string) || "comicrack";
  const autoMatch = parseBooleanField(formData.get("auto_match"));

  return ok({
    file,
    options: {
      importer,
      autoMatch,
    },
  });
}

/**
 * Parse shelf creation form data from FormData (multipart).
 *
 * Parameters
 * ----------
 * formData : FormData
 *     The form data to parse.
 *
 * Returns
 * -------
 * Result<ShelfCreationFormData, ValidationError>
 *     Parsed form data or validation error.
 */
export function parseShelfCreationFormData(
  formData: FormData,
): Result<ShelfCreationFormData, ValidationError> {
  const shelfJson = formData.get("shelf");

  if (typeof shelfJson !== "string") {
    return err(new ValidationError("Missing shelf data"));
  }

  let shelfBody: ShelfCreate;
  try {
    shelfBody = JSON.parse(shelfJson) as ShelfCreate;
  } catch {
    return err(new ValidationError("Invalid shelf JSON"));
  }

  const file = formData.get("file") as File | null;
  const importer = (formData.get("importer") as string) || "comicrack";
  const autoMatch = parseBooleanField(formData.get("auto_match"));

  return ok({
    shelf: shelfBody,
    file,
    importOptions: {
      importer,
      autoMatch,
    },
  });
}

/**
 * Parse shelf creation data from JSON request.
 *
 * Parameters
 * ----------
 * request : Request
 *     The request to parse.
 *
 * Returns
 * -------
 * Promise<Result<ShelfCreate, ValidationError>>
 *     Parsed shelf data or validation error.
 */
export async function parseShelfCreationJson(
  request: Request,
): Promise<Result<ShelfCreate, ValidationError>> {
  try {
    const body = await request.json();
    return ok(body as ShelfCreate);
  } catch {
    return err(new ValidationError("Invalid JSON in request body"));
  }
}

/**
 * Parse ID parameter from route params.
 *
 * Parameters
 * ----------
 * params : Promise<{ id: string }>
 *     Route parameters.
 * paramName : string
 *     Name of the parameter to parse (default: "id").
 *
 * Returns
 * -------
 * Promise<Result<number, ValidationError>>
 *     Parsed ID or validation error.
 */
export async function parseIdParam(
  params: Promise<{ [key: string]: string }>,
  paramName: string = "id",
): Promise<Result<number, ValidationError>> {
  const resolved = await params;
  const idStr = resolved[paramName];

  if (!idStr) {
    return err(new ValidationError(`Missing ${paramName} parameter`));
  }

  const id = parseInt(idStr, 10);

  if (Number.isNaN(id)) {
    return err(new ValidationError(`Invalid ${paramName}: must be a number`));
  }

  return ok(id);
}
