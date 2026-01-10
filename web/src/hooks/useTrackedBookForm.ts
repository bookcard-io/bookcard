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

import { zodResolver } from "@hookform/resolvers/zod";
import { useCallback, useEffect, useRef, useState } from "react";
import { type UseFormReturn, useForm } from "react-hook-form";
import {
  type TrackedBookUpdateFormData,
  trackedBookUpdateSchema,
} from "@/schemas/trackedBookUpdateSchema";
import {
  MonitorMode,
  type TrackedBook,
  type TrackedBookUpdate,
} from "@/types/trackedBook";

export interface UseTrackedBookFormOptions {
  /** Tracked book data to initialize form from. */
  book: TrackedBook | null;
  /** Callback when tracked book is successfully updated. */
  onUpdateSuccess?: (updatedBook: TrackedBook) => void;
  /** Function to update the tracked book. */
  updateBook: (update: TrackedBookUpdate) => Promise<TrackedBook | null>;
}

export interface UseTrackedBookFormResult {
  /** React Hook Form instance. */
  form: UseFormReturn<TrackedBookUpdateFormData>;
  /** Whether form has unsaved changes. */
  hasChanges: boolean;
  /** Whether update was successful. */
  showSuccess: boolean;
  /** Handler for programmatic field changes. */
  handleFieldChange: <K extends keyof TrackedBookUpdateFormData>(
    field: K,
    value: TrackedBookUpdateFormData[K],
  ) => void;
  /** Handler for form submission. */
  handleSubmit: (e: React.FormEvent) => Promise<boolean>;
  /** Reset form to initial state. */
  resetForm: () => void;
}

/**
 * Custom hook for managing tracked book edit form state and submission.
 *
 * Follows the same shape and validation flow as `useBookForm`, but targets
 * tracked-book updates.
 *
 * Parameters
 * ----------
 * options : UseTrackedBookFormOptions
 *     Configuration options including tracked book data and update function.
 *
 * Returns
 * -------
 * UseTrackedBookFormResult
 *     Form state and control functions.
 */
export function useTrackedBookForm({
  book,
  onUpdateSuccess,
  updateBook,
}: UseTrackedBookFormOptions): UseTrackedBookFormResult {
  const [showSuccess, setShowSuccess] = useState(false);
  const [lastBookId, setLastBookId] = useState<number | null>(null);
  const justUpdatedRef = useRef(false);
  const initialFormDataRef = useRef<TrackedBookUpdateFormData | null>(null);

  const bookToFormData = useCallback(
    (b: TrackedBook): TrackedBookUpdateFormData => {
      return {
        title: b.title,
        author: b.author,
        isbn: b.isbn ?? null,
        cover_url: b.cover_url ?? null,
        description: b.description ?? null,
        publisher: b.publisher ?? null,
        published_date: b.published_date ?? null,
        rating: b.rating ?? null,
        tags: b.tags && b.tags.length > 0 ? b.tags : null,
        series_name: b.series_name ?? null,
        series_index: b.series_index ?? null,
        status: b.status,
        monitor_mode: b.monitor_mode ?? MonitorMode.BOOK_ONLY,
        auto_search_enabled: b.auto_search_enabled ?? true,
        auto_download_enabled: b.auto_download_enabled ?? false,
        preferred_formats:
          b.preferred_formats && b.preferred_formats.length > 0
            ? b.preferred_formats
            : null,
        exclude_keywords:
          b.exclude_keywords && b.exclude_keywords.length > 0
            ? b.exclude_keywords
            : null,
        require_keywords:
          b.require_keywords && b.require_keywords.length > 0
            ? b.require_keywords
            : null,
        require_title_match: b.require_title_match ?? true,
        require_author_match: b.require_author_match ?? true,
        require_isbn_match: b.require_isbn_match ?? false,
      };
    },
    [],
  );

  const form = useForm<TrackedBookUpdateFormData>({
    resolver: zodResolver(trackedBookUpdateSchema),
    mode: "onBlur",
    defaultValues: book
      ? bookToFormData(book)
      : ({} as TrackedBookUpdateFormData),
  });

  const hasChanges = form.formState.isDirty;

  useEffect(() => {
    if (book && book.id !== lastBookId) {
      const initialFormData = bookToFormData(book);
      form.reset(initialFormData, { keepDefaultValues: false });
      initialFormDataRef.current = initialFormData;
      setLastBookId(book.id);
      if (lastBookId !== null && !justUpdatedRef.current) {
        setShowSuccess(false);
      }
      justUpdatedRef.current = false;
    } else if (book && book.id === lastBookId && justUpdatedRef.current) {
      const updatedFormData = bookToFormData(book);
      form.reset(updatedFormData, { keepDefaultValues: false });
      initialFormDataRef.current = updatedFormData;
      justUpdatedRef.current = false;
    }
  }, [book, lastBookId, bookToFormData, form]);

  const handleFieldChange = useCallback(
    <K extends keyof TrackedBookUpdateFormData>(
      field: K,
      value: TrackedBookUpdateFormData[K],
    ) => {
      form.setValue(field, value as never, {
        shouldDirty: true,
        shouldValidate: true,
      });
    },
    [form],
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent): Promise<boolean> => {
      e.preventDefault();
      if (!book?.id) {
        return false;
      }

      const isValid = await form.trigger();
      if (!isValid) {
        return false;
      }

      const formData = form.getValues();
      const payload: TrackedBookUpdate = { ...formData };

      // Clean up empty arrays - convert to null for backend
      const cleanedPayload: TrackedBookUpdate = { ...payload };
      if (cleanedPayload.tags && cleanedPayload.tags.length === 0) {
        cleanedPayload.tags = null;
      }
      if (
        cleanedPayload.preferred_formats &&
        cleanedPayload.preferred_formats.length === 0
      ) {
        cleanedPayload.preferred_formats = null;
      }
      if (
        cleanedPayload.exclude_keywords &&
        cleanedPayload.exclude_keywords.length === 0
      ) {
        cleanedPayload.exclude_keywords = null;
      }
      if (
        cleanedPayload.require_keywords &&
        cleanedPayload.require_keywords.length === 0
      ) {
        cleanedPayload.require_keywords = null;
      }

      try {
        const updated = await updateBook(cleanedPayload);
        if (updated) {
          justUpdatedRef.current = true;
          setShowSuccess(true);
          setTimeout(() => setShowSuccess(false), 3000);
          const updatedFormData = bookToFormData(updated);
          form.reset(updatedFormData);
          onUpdateSuccess?.(updated);
          return true;
        }
        return false;
      } catch (_err) {
        return false;
      }
    },
    [book?.id, form, updateBook, onUpdateSuccess, bookToFormData, book],
  );

  const resetForm = useCallback(() => {
    if (hasChanges && initialFormDataRef.current) {
      form.reset(initialFormDataRef.current);
    }
    setShowSuccess(false);
    setLastBookId(null);
  }, [hasChanges, form]);

  return {
    form,
    hasChanges,
    showSuccess,
    handleFieldChange,
    handleSubmit,
    resetForm,
  };
}
