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

import type {
  AuthorListResponse,
  AuthorUpdate,
  AuthorWithMetadata,
} from "@/types/author";

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
  // Normalize authorId: strip any leading /authors/ or / prefix
  const normalizedId = authorId.replace(/^\/authors\//, "").replace(/^\//, "");
  const response = await fetch(`/api/authors/${normalizedId}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    const errorData = (await response.json()) as { detail?: string };
    throw new Error(errorData.detail || "Failed to fetch author");
  }

  return (await response.json()) as AuthorWithMetadata;
}

/**
 * Fetch authors with pagination.
 *
 * Parameters
 * ----------
 * page : number
 *     Page number (1-indexed, default: 1).
 * pageSize : number
 *     Number of items per page (default: 20).
 * filter : "all" | "unmatched" | undefined
 *     Filter type: "unmatched" to show only unmatched authors, "all" or undefined for all authors.
 *
 * Returns
 * -------
 * Promise<AuthorListResponse>
 *     Paginated authors response.
 *
 * Throws
 * ------
 * Error
 *     If the request fails.
 */
export async function fetchAuthorsPage({
  page,
  pageSize,
  filter,
}: {
  page: number;
  pageSize: number;
  filter?: "all" | "unmatched";
}): Promise<AuthorListResponse> {
  const queryParams = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });

  if (filter === "unmatched") {
    queryParams.set("filter", "unmatched");
  }

  const response = await fetch(`/api/authors?${queryParams.toString()}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    const errorData = (await response.json()) as { detail?: string };
    throw new Error(errorData.detail || "Failed to fetch authors");
  }

  return (await response.json()) as AuthorListResponse;
}

/**
 * Fetch all authors (deprecated - use fetchAuthorsPage for pagination).
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

  const data = (await response.json()) as
    | AuthorListResponse
    | AuthorWithMetadata[];

  // Handle both paginated and non-paginated responses
  if (Array.isArray(data)) {
    return data;
  }
  return data.items;
}

/**
 * Update author metadata.
 *
 * Parameters
 * ----------
 * authorId : string
 *     Author ID (can be numeric ID or OpenLibrary key).
 * update : AuthorUpdate
 *     Author update payload.
 *
 * Returns
 * -------
 * Promise<AuthorWithMetadata>
 *     Updated author data.
 *
 * Throws
 * ------
 * Error
 *     If the update fails.
 */
export async function updateAuthor(
  authorId: string,
  update: AuthorUpdate,
): Promise<AuthorWithMetadata> {
  // Normalize authorId: strip any leading /authors/ or / prefix
  const normalizedId = authorId.replace(/^\/authors\//, "").replace(/^\//, "");
  const response = await fetch(`/api/authors/${normalizedId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(update),
    cache: "no-store",
  });

  if (!response.ok) {
    const errorData = (await response.json()) as { detail?: string };
    throw new Error(errorData.detail || "Failed to update author");
  }

  return (await response.json()) as AuthorWithMetadata;
}

/**
 * Upload an author photo from file.
 *
 * Parameters
 * ----------
 * authorId : string
 *     Author ID (can be numeric ID or OpenLibrary key).
 * file : File
 *     Image file to upload.
 *
 * Returns
 * -------
 * Promise<{ photo_id: number; photo_url: string; file_path: string }>
 *     Photo info with ID, URL, and file path.
 *
 * Throws
 * ------
 * Error
 *     If the upload fails.
 */
export async function uploadAuthorPhoto(
  authorId: string,
  file: File,
): Promise<{ photo_id: number; photo_url: string; file_path: string }> {
  // Normalize authorId: strip any leading /authors/ or / prefix
  const normalizedId = authorId.replace(/^\/authors\//, "").replace(/^\//, "");
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`/api/authors/${normalizedId}/photos`, {
    method: "POST",
    body: formData,
    cache: "no-store",
  });

  if (!response.ok) {
    const errorData = (await response.json()) as { detail?: string };
    throw new Error(errorData.detail || "Failed to upload photo");
  }

  return (await response.json()) as {
    photo_id: number;
    photo_url: string;
    file_path: string;
  };
}

/**
 * Upload an author photo from URL.
 *
 * Parameters
 * ----------
 * authorId : string
 *     Author ID (can be numeric ID or OpenLibrary key).
 * url : string
 *     URL of the image to download and save.
 *
 * Returns
 * -------
 * Promise<{ photo_id: number; photo_url: string; file_path: string }>
 *     Photo info with ID, URL, and file path.
 *
 * Throws
 * ------
 * Error
 *     If the upload fails.
 */
export async function uploadPhotoFromUrl(
  authorId: string,
  url: string,
): Promise<{ photo_id: number; photo_url: string; file_path: string }> {
  // Normalize authorId: strip any leading /authors/ or / prefix
  const normalizedId = authorId.replace(/^\/authors\//, "").replace(/^\//, "");
  const response = await fetch(`/api/authors/${normalizedId}/photos-from-url`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ url }),
    cache: "no-store",
  });

  if (!response.ok) {
    const errorData = (await response.json()) as { detail?: string };
    throw new Error(errorData.detail || "Failed to upload photo from URL");
  }

  return (await response.json()) as {
    photo_id: number;
    photo_url: string;
    file_path: string;
  };
}

/**
 * Delete an author photo.
 *
 * Deletes both the database record and the file from the filesystem
 * in an atomic operation.
 *
 * Parameters
 * ----------
 * authorId : string
 *     Author ID (can be numeric ID or OpenLibrary key).
 * photoId : number
 *     Photo ID to delete.
 *
 * Throws
 * ------
 * Error
 *     If the deletion fails.
 */
export async function deleteAuthorPhoto(
  authorId: string,
  photoId: number,
): Promise<void> {
  // Normalize authorId: strip any leading /authors/ or / prefix
  const normalizedId = authorId.replace(/^\/authors\//, "").replace(/^\//, "");
  const response = await fetch(
    `/api/authors/${normalizedId}/photos/${photoId}`,
    {
      method: "DELETE",
      cache: "no-store",
    },
  );

  if (!response.ok) {
    const errorData = (await response.json()) as { detail?: string };
    throw new Error(errorData.detail || "Failed to delete photo");
  }
}

/**
 * Recommend which author to keep when merging.
 *
 * Parameters
 * ----------
 * authorIds : string[]
 *     List of author IDs to merge.
 *
 * Returns
 * -------
 * Promise<{ recommended_keep_id: string | null; authors: AuthorDetail[] }>
 *     Recommendation with author details.
 *
 * Throws
 * ------
 * Error
 *     If the request fails.
 */
export async function recommendMergeAuthor(authorIds: string[]): Promise<{
  recommended_keep_id: string | null;
  authors: Array<{
    id: string | null;
    key: string | null;
    name: string;
    book_count: number;
    is_verified: boolean;
    metadata_score: number;
    photo_url: string | null;
    relationship_counts?: {
      alternate_names: number;
      remote_ids: number;
      photos: number;
      links: number;
      works: number;
      work_subjects: number;
      similarities: number;
      user_metadata: number;
      user_photos: number;
    };
  }>;
}> {
  const response = await fetch("/api/authors/merge/recommend", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ author_ids: authorIds }),
    cache: "no-store",
  });

  if (!response.ok) {
    const errorData = (await response.json()) as { detail?: string };
    throw new Error(errorData.detail || "Failed to get merge recommendation");
  }

  return (await response.json()) as {
    recommended_keep_id: string | null;
    authors: Array<{
      id: string | null;
      key: string | null;
      name: string;
      book_count: number;
      is_verified: boolean;
      metadata_score: number;
      photo_url: string | null;
      relationship_counts?: {
        alternate_names: number;
        remote_ids: number;
        photos: number;
        links: number;
        works: number;
        work_subjects: number;
        similarities: number;
        user_metadata: number;
        user_photos: number;
      };
    }>;
  };
}

/**
 * Merge multiple authors into one.
 *
 * Parameters
 * ----------
 * authorIds : string[]
 *     List of author IDs to merge.
 * keepAuthorId : string
 *     Author ID to keep (others will be merged into this one).
 *
 * Returns
 * -------
 * Promise<{ id: string | null; key: string | null; name: string }>
 *     Merged author details.
 *
 * Throws
 * ------
 * Error
 *     If the merge fails.
 */
export async function mergeAuthors(
  authorIds: string[],
  keepAuthorId: string,
): Promise<{ id: string | null; key: string | null; name: string }> {
  const response = await fetch("/api/authors/merge", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      author_ids: authorIds,
      keep_author_id: keepAuthorId,
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    const errorData = (await response.json()) as { detail?: string };
    throw new Error(errorData.detail || "Failed to merge authors");
  }

  return (await response.json()) as {
    id: string | null;
    key: string | null;
    name: string;
  };
}

/**
 * Rematch an author to a specific OpenLibrary ID.
 *
 * Triggers a single-author workflow: match -> ingest -> link -> score.
 * The match stage will use the provided OpenLibrary key directly,
 * bypassing skip logic.
 *
 * Parameters
 * ----------
 * authorId : string
 *     Author ID (numeric) or OpenLibrary key (e.g., "OL23919A").
 * openlibraryKey : string | undefined
 *     Optional OpenLibrary key to match against. If not provided,
 *     the backend will determine the key.
 *
 * Returns
 * -------
 * Promise<{ message: string; openlibrary_key?: string; library_id?: number }>
 *     Response with message and optional OpenLibrary key.
 *
 * Throws
 * ------
 * Error
 *     If the rematch fails.
 */
export async function rematchAuthor(
  authorId: string,
  openlibraryKey?: string,
): Promise<{ message: string; openlibrary_key?: string; library_id?: number }> {
  // Normalize authorId: strip any leading /authors/ or / prefix
  const normalizedId = authorId.replace(/^\/authors\//, "").replace(/^\//, "");
  const response = await fetch(`/api/authors/${normalizedId}/rematch`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(
      openlibraryKey ? { openlibrary_key: openlibraryKey } : {},
    ),
    cache: "no-store",
  });

  if (!response.ok) {
    const errorData = (await response.json()) as { detail?: string };
    throw new Error(errorData.detail || "Failed to rematch author");
  }

  return (await response.json()) as {
    message: string;
    openlibrary_key?: string;
    library_id?: number;
  };
}
