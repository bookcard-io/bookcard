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

import type { AuthorWithMetadata } from "@/types/author";

/**
 * Fetch a single author by ID.
 *
 * Parameters
 * ----------
 * authorId : string
 *     Author ID (can be numeric ID or OpenLibrary key).
 *
 * Returns
 * -------
 * Promise<AuthorWithMetadata>
 *     Author data.
 *
 * Throws
 * ------
 * Error
 *     If the author is not found or the request fails.
 */
export async function fetchAuthor(
  authorId: string,
): Promise<AuthorWithMetadata> {
  const response = await fetch(`/api/authors/${authorId}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    const errorData = (await response.json()) as { detail?: string };
    throw new Error(errorData.detail || "Failed to fetch author");
  }

  return (await response.json()) as AuthorWithMetadata;
}

/**
 * Fetch all authors.
 *
 * Returns
 * -------
 * Promise<AuthorWithMetadata[]>
 *     Array of all authors.
 *
 * Throws
 * ------
 * Error
 *     If the request fails.
 */
export async function fetchAuthors(): Promise<AuthorWithMetadata[]> {
  const response = await fetch("/api/authors", {
    cache: "no-store",
  });

  if (!response.ok) {
    const errorData = (await response.json()) as { detail?: string };
    throw new Error(errorData.detail || "Failed to fetch authors");
  }

  return (await response.json()) as AuthorWithMetadata[];
}
