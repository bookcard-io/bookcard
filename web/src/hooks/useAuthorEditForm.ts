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
import { useAuthor } from "@/hooks/useAuthor";
import { updateAuthor } from "@/services/authorService";
import type { AuthorUpdate, AuthorWithMetadata } from "@/types/author";

export interface UseAuthorEditFormOptions {
  /** Author ID to edit. */
  authorId: string | null;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when author is saved (for updating display). */
  onAuthorSaved?: (author: AuthorWithMetadata) => void;
}

export interface UseAuthorEditFormResult {
  /** Author data. */
  author: AuthorWithMetadata | null;
  /** Whether author data is loading. */
  isLoading: boolean;
  /** Error message if fetch failed. */
  error: string | null;
  /** Form data. */
  formData: AuthorUpdate;
  /** Whether form has unsaved changes. */
  hasChanges: boolean;
  /** Whether update was successful. */
  showSuccess: boolean;
  /** Whether update is in progress. */
  isUpdating: boolean;
  /** Error message if update failed. */
  updateError: string | null;
  /** Currently staged photo URL. */
  stagedPhotoUrl: string | null;
  /** Handler for field changes. */
  handleFieldChange: <K extends keyof AuthorUpdate>(
    field: K,
    value: AuthorUpdate[K],
  ) => void;
  /** Handler for form submission. */
  handleSubmit: (e: React.FormEvent) => Promise<void>;
  /** Handler for closing the modal (with cleanup). */
  handleClose: () => void;
  /** Handler for photo save completion. */
  handlePhotoSaved: () => void;
}

/**
 * Custom hook for managing author edit form business logic.
 *
 * Handles author data fetching, form state management, and form lifecycle.
 * Follows SRP by separating form logic from modal state.
 * Uses IOC by accepting callbacks as dependencies.
 *
 * Parameters
 * ----------
 * options : UseAuthorEditFormOptions
 *     Configuration including author ID and callbacks.
 *
 * Returns
 * -------
 * UseAuthorEditFormResult
 *     Form state and all handlers needed for the form UI.
 */
export function useAuthorEditForm({
  authorId,
  onClose,
  onAuthorSaved,
}: UseAuthorEditFormOptions): UseAuthorEditFormResult {
  const { author, isLoading, error } = useAuthor({
    authorId,
    enabled: authorId !== null,
  });

  const [formData, setFormData] = useState<AuthorUpdate>({});
  const [hasChanges, setHasChanges] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [stagedPhotoUrl, setStagedPhotoUrl] = useState<string | null>(null);
  const [lastAuthorId, setLastAuthorId] = useState<string | null>(null);
  const initialFormDataRef = useRef<AuthorUpdate>({});

  // Helper function to convert author to form data
  const authorToFormData = useCallback(
    (authorData: AuthorWithMetadata): AuthorUpdate => {
      return {
        name: authorData.name,
        personal_name: authorData.personal_name || null,
        fuller_name: authorData.fuller_name || null,
        title: authorData.title || null,
        birth_date: authorData.birth_date || null,
        death_date: authorData.death_date || null,
        entity_type: authorData.entity_type || null,
        biography: authorData.bio?.value || null,
        location: authorData.location || null,
        photo_url: authorData.photo_url || null,
      };
    },
    [],
  );

  // Initialize form data when author loads or changes
  useEffect(() => {
    if (author && author.key !== lastAuthorId) {
      const initialData = authorToFormData(author);
      setFormData(initialData);
      initialFormDataRef.current = initialData;
      setLastAuthorId(author.key || null);
      setHasChanges(false);
      setShowSuccess(false);
      setUpdateError(null);
      setStagedPhotoUrl(null);
    }
  }, [author, lastAuthorId, authorToFormData]);

  /**
   * Handles field changes in the form.
   */
  const handleFieldChange = useCallback(
    <K extends keyof AuthorUpdate>(field: K, value: AuthorUpdate[K]) => {
      setFormData((prev) => {
        const updated = { ...prev, [field]: value };
        // Check if form has changes compared to initial data
        const hasFormChanges =
          JSON.stringify(updated) !==
          JSON.stringify(initialFormDataRef.current);
        setHasChanges(hasFormChanges);
        return updated;
      });
      setUpdateError(null);
    },
    [],
  );

  /**
   * Handles form submission.
   */
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!author || !hasChanges || isUpdating || !author.key) {
        return;
      }

      setIsUpdating(true);
      setUpdateError(null);
      setShowSuccess(false);

      try {
        const updatedAuthor = await updateAuthor(author.key, formData);

        setShowSuccess(true);
        setHasChanges(false);
        initialFormDataRef.current = { ...formData };

        // Call callback with updated author
        onAuthorSaved?.(updatedAuthor);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to update author";
        setUpdateError(message);
      } finally {
        setIsUpdating(false);
      }
    },
    [author, formData, hasChanges, isUpdating, onAuthorSaved],
  );

  /**
   * Handles closing the modal with cleanup.
   */
  const handleClose = useCallback(() => {
    setFormData(initialFormDataRef.current);
    setHasChanges(false);
    setShowSuccess(false);
    setUpdateError(null);
    setStagedPhotoUrl(null);
    onClose();
  }, [onClose]);

  /**
   * Handles photo save completion.
   */
  const handlePhotoSaved = useCallback(() => {
    // Update photo URL in form data if photo was saved
    // This will be implemented when photo upload is added
    setStagedPhotoUrl(null);
  }, []);

  return {
    author,
    isLoading,
    error,
    formData,
    hasChanges,
    showSuccess,
    isUpdating,
    updateError,
    stagedPhotoUrl,
    handleFieldChange,
    handleSubmit,
    handleClose,
    handlePhotoSaved,
  };
}
