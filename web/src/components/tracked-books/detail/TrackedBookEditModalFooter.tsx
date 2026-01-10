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

import type { FieldErrors } from "react-hook-form";
import { Button } from "@/components/forms/Button";
import type { TrackedBookUpdateFormData } from "@/schemas/trackedBookUpdateSchema";

export interface TrackedBookEditModalFooterProps {
  /** Error message from update attempt. */
  updateError: string | null;
  /** Form validation errors. */
  formErrors: FieldErrors<TrackedBookUpdateFormData>;
  /** Whether to show success message. */
  showSuccess: boolean;
  /** Whether update is in progress. */
  isUpdating: boolean;
  /** Whether form has unsaved changes. */
  hasChanges: boolean;
  /** Callback when cancel is clicked. */
  onCancel: () => void;
  /** Handler for field changes (for metadata import patterns parity). */
  handleFieldChange: <K extends keyof TrackedBookUpdateFormData>(
    field: K,
    value: TrackedBookUpdateFormData[K],
  ) => void;
}

/**
 * Footer component for tracked book edit modal.
 *
 * Mirrors `BookEditModalFooter` validation/error/success presentation.
 */
export function TrackedBookEditModalFooter({
  updateError,
  formErrors,
  showSuccess,
  isUpdating,
  hasChanges,
  onCancel,
}: TrackedBookEditModalFooterProps) {
  const fieldLabels: Record<string, string> = {
    title: "Title",
    author: "Author",
    isbn: "ISBN",
    cover_url: "Cover URL",
    publisher: "Publisher",
    published_date: "Published",
    series_name: "Series",
    series_index: "Series #",
    status: "Status",
    monitor_mode: "Monitor mode",
    preferred_formats: "Preferred formats",
    tags: "Tags",
    exclude_keywords: "Exclude keywords",
    require_keywords: "Required keywords",
    require_title_match: "Require title match",
    require_author_match: "Require author match",
    require_isbn_match: "Require ISBN match",
    description: "Description",
  };

  const validationErrors = Object.entries(formErrors)
    .map(([field, error]) => {
      const message = (error as { message?: string } | undefined)?.message;
      if (message) {
        const fieldLabel = fieldLabels[field] || field;
        return `${fieldLabel}: ${message}`;
      }
      return null;
    })
    .filter((msg): msg is string => msg !== null);

  const hasValidationErrors = validationErrors.length > 0;

  return (
    <div className="modal-footer-between">
      <div className="flex w-full flex-1 flex-col gap-2">
        {hasValidationErrors && (
          <div
            className="rounded-md border border-danger-a0 bg-danger-a20 px-4 py-3 text-danger-a0 text-sm"
            role="alert"
          >
            <div className="mb-1 font-semibold">
              Please fix the following errors:
            </div>
            <ul className="list-inside list-disc space-y-1">
              {validationErrors.map((error) => (
                <li key={error}>{error}</li>
              ))}
            </ul>
          </div>
        )}

        {updateError && (
          <div
            className="rounded-md bg-danger-a20 px-4 py-3 text-danger-a0 text-sm"
            role="alert"
          >
            {updateError}
          </div>
        )}

        {showSuccess && (
          <div className="animate-[slideIn_0.3s_ease-out] rounded-md bg-success-a20 px-4 py-3 text-sm text-success-a0">
            Tracked book updated successfully!
          </div>
        )}
      </div>

      <div className="flex w-full flex-shrink-0 flex-col-reverse justify-end gap-3 md:w-auto md:flex-row">
        <Button
          type="button"
          variant="ghost"
          size="xsmall"
          className="sm:px-6 sm:py-3 sm:text-base"
          onClick={onCancel}
          disabled={isUpdating}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          variant="primary"
          size="xsmall"
          className="sm:px-6 sm:py-3 sm:text-base"
          loading={isUpdating}
          disabled={!hasChanges || hasValidationErrors}
        >
          Save info
        </Button>
      </div>
    </div>
  );
}
