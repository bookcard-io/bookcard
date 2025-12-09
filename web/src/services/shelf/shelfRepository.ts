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
import {
  buildImportFormData,
  parseJsonResponse,
} from "@/libs/response/handlers";
import type { Result } from "@/libs/result";
import type { ImportResult, Shelf, ShelfCreate } from "@/types/shelf";
import type { HttpClient } from "../http/HttpClient";

/**
 * Repository interface for shelf data access.
 *
 * Follows Repository pattern and Dependency Inversion Principle,
 * allowing for easy testing and implementation swapping.
 */
export interface ShelfRepository {
  /**
   * List all shelves.
   *
   * Returns
   * -------
   * Promise<Result<Shelf[], ApiError>>
   *     List of shelves or error.
   */
  list(): Promise<Result<Shelf[], ApiError>>;

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
  create(data: ShelfCreate): Promise<Result<Shelf, ApiError>>;

  /**
   * Import a read list file into a shelf.
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
  importReadList(
    shelfId: number,
    file: File,
    options: { importer: string; autoMatch: boolean },
  ): Promise<Result<ImportResult, ApiError>>;
}

/**
 * HTTP implementation of ShelfRepository.
 */
export class HttpShelfRepository implements ShelfRepository {
  constructor(private readonly client: HttpClient) {}

  /**
   * List all shelves.
   *
   * Returns
   * -------
   * Promise<Result<Shelf[], ApiError>>
   *     List of shelves or error.
   */
  async list(): Promise<Result<Shelf[], ApiError>> {
    const response = await this.client.request("/shelves", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    return parseJsonResponse<Shelf[]>(response, "Failed to fetch shelves");
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
    const response = await this.client.request("/shelves", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    return parseJsonResponse<Shelf>(response, "Failed to create shelf");
  }

  /**
   * Import a read list file into a shelf.
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
    const formData = buildImportFormData(file, options);

    const response = await this.client.request(`/shelves/${shelfId}/import`, {
      method: "POST",
      headers: {},
      body: formData,
    });

    return parseJsonResponse<ImportResult>(
      response,
      "Failed to import read list",
    );
  }
}
