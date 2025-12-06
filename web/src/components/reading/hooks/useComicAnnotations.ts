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

"use client";

import { useCallback, useEffect, useState } from "react";

export interface ComicAnnotation {
  id: number;
  page_number: number;
  x: number;
  y: number;
  width: number;
  height: number;
  type: "highlight" | "bookmark" | "note";
  note?: string;
  annot_id: string;
  created_at: string;
  updated_at: string;
}

export interface ComicAnnotationCreate {
  page_number: number;
  x: number;
  y: number;
  width: number;
  height: number;
  type: "highlight" | "bookmark" | "note";
  note?: string;
}

export interface UseComicAnnotationsOptions {
  bookId: number;
  format: string;
  enabled?: boolean;
}

export interface UseComicAnnotationsResult {
  annotations: ComicAnnotation[];
  isLoading: boolean;
  error: string | null;
  createAnnotation: (
    annotation: ComicAnnotationCreate,
  ) => Promise<ComicAnnotation>;
  updateAnnotation: (
    id: number,
    annotation: Partial<ComicAnnotationCreate>,
  ) => Promise<ComicAnnotation>;
  deleteAnnotation: (id: number) => Promise<void>;
  getAnnotationsForPage: (pageNumber: number) => ComicAnnotation[];
  refetch: () => void;
}

/**
 * Hook for managing comic book annotations.
 *
 * Fetches and manages page-based annotations for comics.
 * Follows SRP by focusing solely on annotation data management.
 *
 * Parameters
 * ----------
 * options : UseComicAnnotationsOptions
 *     Options including book ID and format.
 *
 * Returns
 * -------
 * UseComicAnnotationsResult
 *     Annotation list, loading state, and CRUD methods.
 */
export function useComicAnnotations({
  bookId,
  format,
  enabled = true,
}: UseComicAnnotationsOptions): UseComicAnnotationsResult {
  const [annotations, setAnnotations] = useState<ComicAnnotation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnnotations = useCallback(async () => {
    if (!enabled || !bookId || !format) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Note: This assumes annotation API endpoints exist
      // For now, we'll use a placeholder that can be implemented later
      const response = await fetch(
        `/api/reading/annotations?book_id=${bookId}&format=${format}`,
        {
          method: "GET",
          credentials: "include",
        },
      );

      if (!response.ok) {
        if (response.status === 404) {
          // No annotations endpoint yet - return empty list
          setAnnotations([]);
          setIsLoading(false);
          return;
        }
        const errorData = await response
          .json()
          .catch(() => ({ detail: "Failed to fetch annotations" }));
        throw new Error(errorData.detail || "Failed to fetch annotations");
      }

      const data = (await response.json()) as ComicAnnotation[];
      setAnnotations(data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch annotations";
      setError(errorMessage);
      setAnnotations([]);
    } finally {
      setIsLoading(false);
    }
  }, [bookId, format, enabled]);

  useEffect(() => {
    void fetchAnnotations();
  }, [fetchAnnotations]);

  const createAnnotation = useCallback(
    async (annotation: ComicAnnotationCreate): Promise<ComicAnnotation> => {
      const annotData = JSON.stringify({
        page_number: annotation.page_number,
        x: annotation.x,
        y: annotation.y,
        width: annotation.width,
        height: annotation.height,
        type: annotation.type,
        note: annotation.note,
      });

      const response = await fetch("/api/reading/annotations", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          book_id: bookId,
          format,
          annot_type: annotation.type,
          annot_data: annotData,
          timestamp: Date.now() / 1000,
        }),
      });

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ detail: "Failed to create annotation" }));
        throw new Error(errorData.detail || "Failed to create annotation");
      }

      const created = (await response.json()) as ComicAnnotation;
      setAnnotations((prev) => [...prev, created]);
      return created;
    },
    [bookId, format],
  );

  const updateAnnotation = useCallback(
    async (
      id: number,
      annotation: Partial<ComicAnnotationCreate>,
    ): Promise<ComicAnnotation> => {
      const existing = annotations.find((a) => a.id === id);
      if (!existing) {
        throw new Error("Annotation not found");
      }

      const annotData = JSON.stringify({
        page_number: annotation.page_number ?? existing.page_number,
        x: annotation.x ?? existing.x,
        y: annotation.y ?? existing.y,
        width: annotation.width ?? existing.width,
        height: annotation.height ?? existing.height,
        type: annotation.type ?? existing.type,
        note: annotation.note ?? existing.note,
      });

      const response = await fetch(`/api/reading/annotations/${id}`, {
        method: "PUT",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          annot_data: annotData,
        }),
      });

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ detail: "Failed to update annotation" }));
        throw new Error(errorData.detail || "Failed to update annotation");
      }

      const updated = (await response.json()) as ComicAnnotation;
      setAnnotations((prev) => prev.map((a) => (a.id === id ? updated : a)));
      return updated;
    },
    [annotations],
  );

  const deleteAnnotation = useCallback(async (id: number): Promise<void> => {
    const response = await fetch(`/api/reading/annotations/${id}`, {
      method: "DELETE",
      credentials: "include",
    });

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Failed to delete annotation" }));
      throw new Error(errorData.detail || "Failed to delete annotation");
    }

    setAnnotations((prev) => prev.filter((a) => a.id !== id));
  }, []);

  const getAnnotationsForPage = useCallback(
    (pageNumber: number): ComicAnnotation[] => {
      return annotations.filter((a) => a.page_number === pageNumber);
    },
    [annotations],
  );

  return {
    annotations,
    isLoading,
    error,
    createAnnotation,
    updateAnnotation,
    deleteAnnotation,
    getAnnotationsForPage,
    refetch: fetchAnnotations,
  };
}
