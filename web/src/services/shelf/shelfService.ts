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

import type { ApiError } from "@/libs/errors";
import type { Result } from "@/libs/result";
import type { ImportResult, Shelf, ShelfCreate } from "@/types/shelf";
import type { ShelfRepository } from "./shelfRepository";

/**
 * Service for shelf business logic.
 *
 * Orchestrates shelf operations and follows Single Responsibility Principle
 * by separating business logic from data access.
 */
export class ShelfService {
  constructor(private readonly repository: ShelfRepository) {}

  /**
   * List all shelves.
   *
   * Returns
   * -------
   * Promise<Result<Shelf[], ApiError>>
   *     List of shelves or error.
   */
  async list(): Promise<Result<Shelf[], ApiError>> {
    return this.repository.list();
  }

  /**
   * Create a new shelf.
   *
   * Parameters
   * ----------
   * data : ShelfCreate
   *     Shelf creation data.
   *
   * Returns
   * -------
   * Promise<Result<Shelf, ApiError>>
   *     Created shelf or error.
   */
  async create(data: ShelfCreate): Promise<Result<Shelf, ApiError>> {
    return this.repository.create(data);
  }

  /**
   * Create a shelf and optionally import a read list file.
   *
   * Parameters
   * ----------
   * shelfData : ShelfCreate
   *     Shelf creation data.
   * file : File | null
   *     Optional read list file to import.
   * importOptions : { importer: string; autoMatch: boolean }
   *     Import options (only used if file is provided).
   *
   * Returns
   * -------
   * Promise<Result<Shelf, ApiError>>
   *     Created shelf or error. If file is provided and import fails,
   *     the shelf is still returned (import errors are logged but
   *     don't fail the operation).
   */
  async createWithImport(
    shelfData: ShelfCreate,
    file: File | null,
    importOptions: { importer: string; autoMatch: boolean },
  ): Promise<Result<Shelf, ApiError>> {
    // First, create the shelf
    const createResult = await this.repository.create(shelfData);

    if (createResult.isErr) {
      return createResult;
    }

    const shelf = createResult.value;

    // If no file provided, just return the created shelf
    if (!file) {
      return createResult;
    }

    // Import the file (we intentionally ignore import errors here
    // and return the shelf, since callers expect a Shelf object)
    const importResult = await this.repository.importReadList(
      shelf.id,
      file,
      importOptions,
    );

    if (importResult.isErr) {
      // Log but don't fail - the shelf was created successfully
      console.error("Failed to import read list:", importResult.error);
    }

    return createResult;
  }

  /**
   * Import a read list file into an existing shelf.
   *
   * Parameters
   * ----------
   * shelfId : number
   *     The shelf ID to import into.
   * file : File
   *     The read list file to import.
   * options : { importer: string; autoMatch: boolean }
   *     Import options.
   *
   * Returns
   * -------
   * Promise<Result<ImportResult, ApiError>>
   *     Import result or error.
   */
  async importReadList(
    shelfId: number,
    file: File,
    options: { importer: string; autoMatch: boolean },
  ): Promise<Result<ImportResult, ApiError>> {
    return this.repository.importReadList(shelfId, file, options);
  }
}
