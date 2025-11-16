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

import { useCallback } from "react";
import { Button } from "@/components/forms/Button";
import { useUser } from "@/contexts/UserContext";

export interface BookEditModalFooterProps {
  /** Book ID for metadata download. */
  bookId: number;
  /** Error message from update attempt. */
  updateError: string | null;
  /** Whether to show success message. */
  showSuccess: boolean;
  /** Whether update is in progress. */
  isUpdating: boolean;
  /** Whether form has unsaved changes. */
  hasChanges: boolean;
  /** Callback when cancel is clicked. */
  onCancel: () => void;
}

/**
 * Footer component for book edit modal.
 *
 * Displays status messages and action buttons.
 * Follows SRP by focusing solely on footer presentation.
 */
export function BookEditModalFooter({
  bookId,
  updateError,
  showSuccess,
  isUpdating,
  hasChanges,
  onCancel,
}: BookEditModalFooterProps) {
  const { getSetting } = useUser();

  /**
   * Handles downloading book metadata in the user's preferred format.
   */
  const handleDownloadMetadata = useCallback(async () => {
    try {
      // Get user's preferred format, default to 'opf'
      const format = getSetting("metadata_download_format") || "opf";

      const downloadUrl = `/api/books/${bookId}/metadata?format=${format}`;
      const response = await fetch(downloadUrl, {
        method: "GET",
      });
      if (!response.ok) {
        // eslint-disable-next-line no-console
        console.error("Download failed", await response.text());
        return;
      }
      const blob = await response.blob();
      const contentDisposition = response.headers.get("content-disposition");
      let filename = `book_${bookId}_metadata.${format}`;
      if (contentDisposition) {
        const match = contentDisposition.match(
          /filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i,
        );
        const cdName = decodeURIComponent(match?.[1] || match?.[2] || "");
        if (cdName) {
          filename = cdName;
        }
      }
      const objectUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(objectUrl);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error("Download error", err);
    }
  }, [bookId, getSetting]);

  return (
    <div className="flex flex-col gap-4 border-surface-a20 border-t bg-surface-tonal-a10 p-4 md:flex-row md:items-center md:justify-between md:gap-4 md:px-6 md:pt-4 md:pb-6">
      <div className="flex w-full flex-1 flex-col gap-2">
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
            Book metadata updated successfully!
          </div>
        )}
      </div>
      <div className="flex w-full flex-shrink-0 flex-col-reverse justify-end gap-3 md:w-auto md:flex-row">
        <Button
          type="button"
          variant="secondary"
          size="xsmall"
          className="sm:px-6 sm:py-3 sm:text-base"
          onClick={() => {}}
          disabled={isUpdating}
        >
          Import metadata
        </Button>
        <Button
          type="button"
          variant="secondary"
          size="xsmall"
          className="sm:px-6 sm:py-3 sm:text-base"
          onClick={handleDownloadMetadata}
          disabled={isUpdating}
        >
          Download metadata
        </Button>
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
          disabled={!hasChanges}
        >
          Save info
        </Button>
      </div>
    </div>
  );
}
