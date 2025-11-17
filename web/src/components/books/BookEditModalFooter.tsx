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

import { useCallback, useRef } from "react";
import { Button } from "@/components/forms/Button";
import { useUser } from "@/contexts/UserContext";
import type { BookUpdate } from "@/types/book";
import { applyBookUpdateToForm } from "@/utils/metadata";
import { parseJsonMetadataFile } from "@/utils/metadataImport";

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
  /** Handler for field changes. */
  handleFieldChange: <K extends keyof BookUpdate>(
    field: K,
    value: BookUpdate[K],
  ) => void;
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
  handleFieldChange,
}: BookEditModalFooterProps) {
  const { getSetting } = useUser();
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  /**
   * Handles importing metadata from file.
   *
   * Opens file picker and parses the selected file (YAML, JSON, or OPF),
   * then stages the metadata in the form without applying it.
   */
  const handleImportMetadata = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  /**
   * Handles file selection and parsing.
   *
   * JSON files are parsed client-side, while OPF and YAML files
   * are sent to the backend for processing.
   */
  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) {
        return;
      }

      // Reset file input so same file can be selected again
      e.target.value = "";

      const fileName = file.name.toLowerCase();
      const extension = fileName.split(".").pop()?.toLowerCase() || "";

      try {
        let update: BookUpdate;

        if (extension === "json") {
          // Parse JSON client-side
          update = await parseJsonMetadataFile(file);
        } else if (
          extension === "opf" ||
          extension === "yaml" ||
          extension === "yml"
        ) {
          // Send OPF/YAML to backend for processing
          const formData = new FormData();
          formData.append("file", file);

          const response = await fetch("/api/books/metadata/import", {
            method: "POST",
            body: formData,
          });

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({
              detail: "Failed to import metadata",
            }));
            throw new Error(errorData.detail || "Failed to import metadata");
          }

          update = (await response.json()) as BookUpdate;
        } else {
          throw new Error(
            `Unsupported file format: ${extension}. Supported formats: json, yaml, opf`,
          );
        }

        applyBookUpdateToForm(update, handleFieldChange);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to import metadata";
        // eslint-disable-next-line no-console
        console.error("Import metadata error:", message);
        // TODO: Show error message to user (could add error state prop)
        alert(`Failed to import metadata: ${message}`);
      }
    },
    [handleFieldChange],
  );

  return (
    <div className="modal-footer-between">
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
        <input
          ref={fileInputRef}
          type="file"
          accept=".json,.yaml,.yml,.opf"
          className="hidden"
          onChange={handleFileChange}
          aria-label="Import metadata file"
        />
        <Button
          type="button"
          variant="secondary"
          size="xsmall"
          className="sm:px-6 sm:py-3 sm:text-base"
          onClick={handleImportMetadata}
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
