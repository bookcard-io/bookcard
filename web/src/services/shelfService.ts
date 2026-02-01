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
 * Service for interacting with shelf API endpoints.
 *
 * Provides methods for creating, reading, updating, and deleting shelves,
 * as well as managing book-shelf associations.
 */

import type {
  ImportResult,
  Shelf,
  ShelfCreate,
  ShelfListResponse,
  ShelfUpdate,
} from "@/types/shelf";

const API_BASE = "/api/shelves";

export interface CreateShelfOptions {
  /** Optional read list file (.cbl, etc.) to import when creating the shelf. */
  readListFile?: File | null;
  /** Optional importer name (e.g., "comicrack"). */
  importer?: string;
  /** Whether to automatically add matched books to the shelf. Defaults to true. */
  autoAddMatched?: boolean;
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
 * Promise<Shelf>
 *     Created shelf data.
 */
export async function createShelf(
  data: ShelfCreate,
  options?: CreateShelfOptions,
): Promise<Shelf> {
  const hasReadListFile = options?.readListFile instanceof File;

  const response = hasReadListFile
    ? await fetch(API_BASE, {
        method: "POST",
        credentials: "include",
        body: (() => {
          const formData = new FormData();
          formData.append("shelf", JSON.stringify(data));

          if (options?.readListFile) {
            formData.append("file", options.readListFile);
          }

          const importer = options?.importer || "comicrack";
          formData.append("importer", importer);

          const autoMatch =
            options?.autoAddMatched !== undefined
              ? options.autoAddMatched
              : true;
          formData.append("auto_match", String(autoMatch));

          return formData;
        })(),
      })
    : await fetch(API_BASE, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(data),
      });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to create shelf" }));
    throw new Error(error.detail || "Failed to create shelf");
  }

  return response.json();
}

/**
 * List shelves accessible to the current user.
 *
 * Returns
 * -------
 * Promise<ShelfListResponse>
 *     List of shelves with total count.
 */
export async function listShelves(): Promise<ShelfListResponse> {
  const response = await fetch(API_BASE, {
    method: "GET",
    credentials: "include",
    cache: "no-store",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to list shelves" }));
    throw new Error(error.detail || "Failed to list shelves");
  }

  return response.json();
}

/**
 * Get a shelf by ID.
 *
 * Parameters
 * ----------
 * id : number
 *     Shelf ID.
 *
 * Returns
 * -------
 * Promise<Shelf>
 *     Shelf data.
 */
export async function getShelf(id: number): Promise<Shelf> {
  const response = await fetch(`${API_BASE}/${id}`, {
    method: "GET",
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to get shelf" }));
    throw new Error(error.detail || "Failed to get shelf");
  }

  return response.json();
}

/**
 * Update a shelf.
 *
 * Parameters
 * ----------
 * id : number
 *     Shelf ID to update.
 * data : ShelfUpdate
 *     Shelf update data.
 *
 * Returns
 * -------
 * Promise<Shelf>
 *     Updated shelf data.
 */
export async function updateShelf(
  id: number,
  data: ShelfUpdate,
): Promise<Shelf> {
  const response = await fetch(`${API_BASE}/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to update shelf" }));
    throw new Error(error.detail || "Failed to update shelf");
  }

  return response.json();
}

/**
 * Delete a shelf.
 *
 * Parameters
 * ----------
 * id : number
 *     Shelf ID to delete.
 *
 * Returns
 * -------
 * Promise<void>
 */
export async function deleteShelf(id: number): Promise<void> {
  const response = await fetch(`${API_BASE}/${id}`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to delete shelf" }));
    throw new Error(error.detail || "Failed to delete shelf");
  }
}

/**
 * Add a book to a shelf.
 *
 * Parameters
 * ----------
 * shelfId : number
 *     Shelf ID.
 * bookId : number
 *     Calibre book ID.
 *
 * Returns
 * -------
 * Promise<void>
 */
export async function addBookToShelf(
  shelfId: number,
  bookId: number,
): Promise<void> {
  const response = await fetch(`${API_BASE}/${shelfId}/books/${bookId}`, {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to add book to shelf" }));
    throw new Error(error.detail || "Failed to add book to shelf");
  }
}

/**
 * Remove a book from a shelf.
 *
 * Parameters
 * ----------
 * shelfId : number
 *     Shelf ID.
 * bookId : number
 *     Calibre book ID.
 *
 * Returns
 * -------
 * Promise<void>
 */
export async function removeBookFromShelf(
  shelfId: number,
  bookId: number,
): Promise<void> {
  const response = await fetch(`${API_BASE}/${shelfId}/books/${bookId}`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to remove book from shelf" }));
    throw new Error(error.detail || "Failed to remove book from shelf");
  }
}

/**
 * Reorder books in a shelf.
 *
 * Parameters
 * ----------
 * shelfId : number
 *     Shelf ID.
 * bookOrders : Record<number, number>
 *     Mapping of book_id to new order value.
 *
 * Returns
 * -------
 * Promise<void>
 */
export async function reorderShelfBooks(
  shelfId: number,
  bookOrders: Record<number, number>,
): Promise<void> {
  const response = await fetch(`${API_BASE}/${shelfId}/books/reorder`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ book_orders: bookOrders }),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to reorder shelf books" }));
    throw new Error(error.detail || "Failed to reorder shelf books");
  }
}

/**
 * Get book IDs in a shelf with pagination and sorting.
 *
 * Parameters
 * ----------
 * shelfId : number
 *     Shelf ID.
 * page : number
 *     Page number (1-indexed, default: 1).
 * sortBy : string
 *     Sort field: 'order', 'date_added', or 'book_id' (default: 'order').
 *
 * Returns
 * -------
 * Promise<number[]>
 *     List of book IDs in the shelf.
 */
/**
 * Import a read list from a file into a shelf.
 *
 * Parameters
 * ----------
 * shelfId : number
 *     Shelf ID to import into.
 * importerData : { importer?: string; auto_add_matched?: boolean }
 *     Importer configuration (e.g., importer name, auto-add flag).
 * file : File
 *     Read list file to import (.cbl, etc.).
 *
 * Returns
 * -------
 * Promise<ImportResult>
 *     Import result with matched and unmatched books.
 */
export async function importReadList(
  shelfId: number,
  importerData: { importer?: string; auto_add_matched?: boolean },
  file: File,
): Promise<ImportResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("importer", importerData.importer || "comicrack");
  formData.append("auto_match", String(importerData.auto_add_matched || false));

  const response = await fetch(`${API_BASE}/${shelfId}/import`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Import failed" }));
    throw new Error(error.detail || "Import failed");
  }

  return response.json();
}

export async function getShelfBooks(
  shelfId: number,
  page: number = 1,
  sortBy: string = "order",
): Promise<number[]> {
  const params = new URLSearchParams({
    page: page.toString(),
    sort_by: sortBy,
    sort_order: "asc",
  });

  const response = await fetch(`${API_BASE}/${shelfId}/books?${params}`, {
    method: "GET",
    credentials: "include",
    cache: "no-store",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to get shelf books" }));
    throw new Error(error.detail || "Failed to get shelf books");
  }

  return response.json();
}

/**
 * Upload a shelf's cover picture.
 *
 * Parameters
 * ----------
 * shelfId : number
 *     Shelf identifier.
 * file : File
 *     Image file to upload.
 *
 * Returns
 * -------
 * Promise<Shelf>
 *     Updated shelf data.
 */
export async function uploadShelfCoverPicture(
  shelfId: number,
  file: File,
): Promise<Shelf> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/${shelfId}/cover-picture`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to upload cover picture" }));
    throw new Error(error.detail || "Failed to upload cover picture");
  }

  return response.json();
}

/**
 * Get a shelf's cover picture URL.
 *
 * Parameters
 * ----------
 * shelfId : number
 *     Shelf identifier.
 *
 * Returns
 * -------
 * string
 *     URL to the cover picture.
 */
export function getShelfCoverPictureUrl(shelfId: number): string {
  return `${API_BASE}/${shelfId}/cover-picture`;
}

/**
 * Delete a shelf's cover picture.
 *
 * Parameters
 * ----------
 * shelfId : number
 *     Shelf identifier.
 *
 * Returns
 * -------
 * Promise<Shelf>
 *     Updated shelf data.
 */
export async function deleteShelfCoverPicture(shelfId: number): Promise<Shelf> {
  const response = await fetch(`${API_BASE}/${shelfId}/cover-picture`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to delete cover picture" }));
    throw new Error(error.detail || "Failed to delete cover picture");
  }

  return response.json();
}
