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
 * Hook for shelf create/edit form logic.
 *
 * Manages form state, validation, and submission for shelf creation and editing.
 */

import { useCallback, useState } from "react";
import type { FilterGroup } from "@/types/magicShelf";
import type { ShelfCreate, ShelfUpdate } from "@/types/shelf";

interface UseShelfFormOptions {
  /** Initial shelf name (for edit mode). */
  initialName?: string;
  /** Initial description (for edit mode). */
  initialDescription?: string | null;
  /** Initial public status (for edit mode). */
  initialIsPublic?: boolean;
  /** Initial filter rules (for edit mode). */
  initialFilterRules?: FilterGroup | null;
  /** Callback when form is successfully submitted. */
  onSubmit?: (data: ShelfCreate | ShelfUpdate) => void | Promise<void>;
  /** Callback when form submission fails. */
  onError?: (error: string) => void;
}

interface UseShelfFormReturn {
  /** Current shelf name. */
  name: string;
  /** Current description. */
  description: string;
  /** Current public status. */
  isPublic: boolean;
  /** Current filter rules. */
  filterRules: FilterGroup | null;
  /** Whether form is being submitted. */
  isSubmitting: boolean;
  /** Form validation errors. */
  errors: {
    name?: string;
    description?: string;
    isPublic?: string;
    filterRules?: string;
  };
  /** Update shelf name. */
  setName: (name: string) => void;
  /** Update description. */
  setDescription: (description: string) => void;
  /** Update public status. */
  setIsPublic: (isPublic: boolean) => void;
  /** Update filter rules. */
  setFilterRules: (rules: FilterGroup | null) => void;
  /** Validate and submit the form. */
  handleSubmit: () => Promise<boolean>;
  /** Reset form to initial values. */
  reset: () => void;
}

/**
 * Hook for shelf create/edit form logic.
 *
 * Parameters
 * ----------
 * options : UseShelfFormOptions
 *     Configuration options for the form.
 *
 * Returns
 * -------
 * UseShelfFormReturn
 *     Object with form state and handlers.
 */
export function useShelfForm(
  options: UseShelfFormOptions = {},
): UseShelfFormReturn {
  const {
    initialName = "",
    initialDescription = null,
    initialIsPublic = false,
    initialFilterRules = null,
    onSubmit,
    onError,
  } = options;

  const [name, setName] = useState(initialName);
  const [description, setDescription] = useState(initialDescription ?? "");
  const [isPublic, setIsPublic] = useState(initialIsPublic);
  const [filterRules, setFilterRules] = useState<FilterGroup | null>(
    initialFilterRules,
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<{
    name?: string;
    description?: string;
    isPublic?: string;
    filterRules?: string;
  }>({});

  const validate = useCallback((): boolean => {
    const newErrors: {
      name?: string;
      description?: string;
      isPublic?: string;
      filterRules?: string;
    } = {};

    if (!name.trim()) {
      newErrors.name = "Shelf name is required";
    } else if (name.length > 255) {
      newErrors.name = "Shelf name must be 255 characters or less";
    }

    if (description.length > 5000) {
      newErrors.description = "Description must be 5000 characters or less";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [name, description]);

  const handleSubmit = useCallback(async (): Promise<boolean> => {
    if (!validate()) {
      return false;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      const data: ShelfCreate | ShelfUpdate = {
        name: name.trim(),
        description: description.trim() || null,
        is_public: isPublic,
        filter_rules: filterRules as Record<string, unknown> | null,
      };

      if (onSubmit) {
        await onSubmit(data);
      }

      return true;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to save shelf";
      if (onError) {
        onError(errorMessage);
      }
      setErrors({ name: errorMessage });
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }, [name, description, isPublic, filterRules, validate, onSubmit, onError]);

  const reset = useCallback(() => {
    setName(initialName);
    setDescription(initialDescription ?? "");
    setIsPublic(initialIsPublic);
    setFilterRules(initialFilterRules);
    setErrors({});
    setIsSubmitting(false);
  }, [initialName, initialDescription, initialIsPublic, initialFilterRules]);

  return {
    name,
    description,
    isPublic,
    filterRules,
    isSubmitting,
    errors,
    setName,
    setDescription,
    setIsPublic,
    setFilterRules,
    handleSubmit,
    reset,
  };
}
