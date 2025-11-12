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

import { useCallback, useEffect, useRef, useState } from "react";
import type { Book, BookUpdate } from "@/types/book";

export interface UseBookFormOptions {
  /** Book data to initialize form from. */
  book: Book | null;
  /** Callback when book is successfully updated. */
  onUpdateSuccess?: (updatedBook: Book) => void;
  /** Function to update the book. */
  updateBook: (update: BookUpdate) => Promise<Book | null>;
}

export interface UseBookFormResult {
  /** Current form data. */
  formData: BookUpdate;
  /** Whether form has unsaved changes. */
  hasChanges: boolean;
  /** Whether update was successful. */
  showSuccess: boolean;
  /** Handler for field changes. */
  handleFieldChange: <K extends keyof BookUpdate>(
    field: K,
    value: BookUpdate[K],
  ) => void;
  /** Handler for form submission. */
  handleSubmit: (e: React.FormEvent) => Promise<void>;
  /** Reset form to initial state. */
  resetForm: () => void;
}

/**
 * Custom hook for managing book edit form state and submission.
 *
 * Handles form initialization, field changes, and submission logic.
 * Follows SRP by separating form logic from UI components.
 * Follows DRY by centralizing form state management.
 *
 * Parameters
 * ----------
 * options : UseBookFormOptions
 *     Configuration options including book data and update function.
 *
 * Returns
 * -------
 * UseBookFormResult
 *     Form state and control functions.
 */
export function useBookForm({
  book,
  onUpdateSuccess,
  updateBook,
}: UseBookFormOptions): UseBookFormResult {
  const [formData, setFormData] = useState<BookUpdate>({});
  const [hasChanges, setHasChanges] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [lastBookId, setLastBookId] = useState<number | null>(null);
  const justUpdatedRef = useRef(false);
  // Store initial form data when modal opens to reset on cancel
  const initialFormDataRef = useRef<BookUpdate>({});

  // Helper function to convert book to form data
  const bookToFormData = useCallback((bookData: Book): BookUpdate => {
    // Extract date part from ISO string if present
    let pubdateValue: string | null = null;
    if (bookData.pubdate) {
      const dateMatch = bookData.pubdate.match(/^(\d{4}-\d{2}-\d{2})/);
      if (dateMatch?.[1]) {
        pubdateValue = dateMatch[1];
      }
    }

    return {
      title: bookData.title,
      pubdate: pubdateValue,
      author_names: bookData.authors || [],
      series_name: bookData.series || null,
      series_index: bookData.series_index ?? null,
      tag_names: bookData.tags || [],
      identifiers: bookData.identifiers || [],
      description: bookData.description || null,
      publisher_name: bookData.publisher || null,
      language_codes: bookData.languages || null,
      rating_value: bookData.rating ?? null,
    };
  }, []);

  // Initialize form data when book loads (only on initial load or book ID change)
  useEffect(() => {
    if (book && book.id !== lastBookId) {
      const initialFormData = bookToFormData(book);
      setFormData(initialFormData);
      // Store initial form data for reset on cancel
      initialFormDataRef.current = initialFormData;
      setHasChanges(false);
      setLastBookId(book.id);
      // Only reset success if this is a new book (different ID) and we didn't just update
      if (lastBookId !== null && !justUpdatedRef.current) {
        setShowSuccess(false);
      }
      justUpdatedRef.current = false;
    } else if (book && book.id === lastBookId && justUpdatedRef.current) {
      // Book was just updated (same ID), update form and initial data to reflect saved state
      const updatedFormData = bookToFormData(book);
      setFormData(updatedFormData);
      initialFormDataRef.current = updatedFormData;
      justUpdatedRef.current = false;
    }
  }, [book, lastBookId, bookToFormData]);

  const handleFieldChange = useCallback(
    <K extends keyof BookUpdate>(field: K, value: BookUpdate[K]) => {
      setFormData((prev) => {
        const updated = { ...prev, [field]: value };
        setHasChanges(true);
        return updated;
      });
    },
    [],
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!book?.id) {
        return;
      }

      // Convert date string to ISO format if provided
      const updatePayload: BookUpdate = { ...formData };
      if (updatePayload.pubdate) {
        // If it's just a date string (YYYY-MM-DD), convert to ISO
        if (
          typeof updatePayload.pubdate === "string" &&
          updatePayload.pubdate.match(/^\d{4}-\d{2}-\d{2}$/)
        ) {
          updatePayload.pubdate = `${updatePayload.pubdate}T00:00:00Z`;
        }
      }

      // Clean up empty arrays - convert to null for backend
      const cleanedPayload: BookUpdate = { ...updatePayload };
      if (
        cleanedPayload.author_names &&
        cleanedPayload.author_names.length === 0
      ) {
        cleanedPayload.author_names = null;
      }
      if (cleanedPayload.tag_names && cleanedPayload.tag_names.length === 0) {
        cleanedPayload.tag_names = null;
      }
      if (
        cleanedPayload.identifiers &&
        cleanedPayload.identifiers.length === 0
      ) {
        cleanedPayload.identifiers = null;
      }
      if (
        cleanedPayload.language_codes &&
        cleanedPayload.language_codes.length === 0
      ) {
        cleanedPayload.language_codes = null;
      }

      const updated = await updateBook(cleanedPayload);
      if (updated) {
        setHasChanges(false);
        justUpdatedRef.current = true;
        setShowSuccess(true);
        // Hide success message after 3 seconds
        setTimeout(() => setShowSuccess(false), 3000);
        onUpdateSuccess?.(updated);
      }
    },
    [book?.id, formData, updateBook, onUpdateSuccess],
  );

  const resetForm = useCallback(() => {
    // Only reset if there are unsaved changes
    // If user saved, hasChanges will be false and we shouldn't reset
    if (hasChanges) {
      // Reset to initial form data (from when modal was opened)
      setFormData(initialFormDataRef.current);
      setHasChanges(false);
    }
    setShowSuccess(false);
    // Reset lastBookId so form reinitializes when modal reopens
    setLastBookId(null);
  }, [hasChanges]);

  return {
    formData,
    hasChanges,
    showSuccess,
    handleFieldChange,
    handleSubmit,
    resetForm,
  };
}
