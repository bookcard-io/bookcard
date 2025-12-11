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

import { format } from "date-fns";
import { useEffect, useMemo, useState } from "react";
import { useModal } from "@/hooks/useModal";
import { formatFileSize } from "@/utils/format";

export interface FormatInfoModalProps {
  isOpen: boolean;
  onClose: () => void;
  format: {
    format: string;
    size: number;
  };
  bookId: number;
  bookTitle: string;
}

interface FormatMetadata {
  format: string;
  size: number;
  path: string;
  created_at?: string;
  modified_at?: string;
  version?: string;
  page_count?: number;
  encryption?: string;
  validation_status?: string;
  validation_issues?: string[];
  mime_type?: string;
}

/**
 * Format information modal component.
 *
 * Displays detailed information about a specific book format.
 * Follows SRP by focusing solely on format metadata presentation.
 */
export function FormatInfoModal({
  isOpen,
  onClose,
  format: basicFormatData,
  bookId,
  bookTitle,
}: FormatInfoModalProps) {
  useModal(isOpen);
  const [metadata, setMetadata] = useState<FormatMetadata | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const formatUpper = useMemo(
    () => basicFormatData.format.toUpperCase(),
    [basicFormatData.format],
  );

  useEffect(() => {
    if (isOpen && bookId && basicFormatData.format) {
      setIsLoading(true);
      setError(null);
      setMetadata(null);

      const fetchMetadata = async () => {
        try {
          const response = await fetch(
            `/api/books/${bookId}/formats/${basicFormatData.format}/metadata`,
          );
          if (!response.ok) {
            throw new Error("Failed to fetch format metadata");
          }
          const data = await response.json();
          setMetadata(data);
        } catch (err) {
          setError(err instanceof Error ? err.message : "An error occurred");
        } finally {
          setIsLoading(false);
        }
      };

      fetchMetadata();
    }
  }, [isOpen, bookId, basicFormatData.format]);

  if (!isOpen) {
    return null;
  }

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const renderRow = (label: string, value: string | number | undefined) => {
    if (value === undefined || value === null) return null;
    return (
      <div className="flex flex-col gap-1 border-surface-a10 border-b py-3 last:border-b-0">
        <span className="font-medium text-sm text-text-a30">{label}</span>
        <span className="break-all text-base text-text-a0">{value}</span>
      </div>
    );
  };

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="modal-overlay modal-overlay-z-1002 modal-overlay-padding"
      onClick={handleOverlayClick}
      role="presentation"
    >
      <div
        className="modal-container modal-container-shadow-large w-full max-w-md flex-col"
        role="dialog"
        aria-modal="true"
        aria-label={`${formatUpper} Information`}
      >
        <div className="flex items-center justify-between border-surface-a10 border-b p-4">
          <h2 className="m-0 font-bold text-text-a0 text-xl">
            {formatUpper} Details
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="modal-close-button modal-close-button-sm cursor-pointer transition-all hover:bg-surface-a20 hover:text-text-a0"
            aria-label="Close"
          >
            <i className="pi pi-times" aria-hidden="true" />
          </button>
        </div>

        <div className="flex max-h-[70vh] flex-col overflow-y-auto p-6">
          <div className="mb-4 rounded-md bg-surface-tonal-a10 p-3">
            <span className="text-sm text-text-a30">Book</span>
            <div className="font-medium text-text-a0">{bookTitle}</div>
          </div>

          {isLoading && (
            <div className="flex justify-center p-4">
              <span className="pi pi-spinner pi-spin text-2xl text-primary-a0" />
            </div>
          )}

          {error && (
            <div className="rounded-md bg-error-a10 p-3 text-error-a0 text-sm">
              {error}
            </div>
          )}

          {metadata && (
            <div className="flex flex-col">
              {renderRow("Format", formatUpper)}
              {renderRow("Size", formatFileSize(metadata.size))}
              {renderRow("File Path", metadata.path)}
              {renderRow(
                "Created",
                metadata.created_at
                  ? format(new Date(metadata.created_at), "PPP p")
                  : undefined,
              )}
              {renderRow(
                "Modified",
                metadata.modified_at
                  ? format(new Date(metadata.modified_at), "PPP p")
                  : undefined,
              )}
              {renderRow("Version", metadata.version)}
              {renderRow("Page Count", metadata.page_count)}
              {renderRow("Encryption", metadata.encryption)}
              {renderRow("MIME Type", metadata.mime_type)}
              {renderRow("Validation", metadata.validation_status)}
              {metadata.validation_issues &&
                metadata.validation_issues.length > 0 && (
                  <div className="flex flex-col gap-1 border-surface-a10 border-b py-3 last:border-b-0">
                    <span className="font-medium text-error-a0 text-sm">
                      Issues
                    </span>
                    <ul className="list-inside list-disc text-sm text-text-a0">
                      {metadata.validation_issues.map((issue, i) => (
                        // biome-ignore lint/suspicious/noArrayIndexKey: simple list
                        <li key={i}>{issue}</li>
                      ))}
                    </ul>
                  </div>
                )}
            </div>
          )}

          {!metadata && !isLoading && !error && (
            <div className="flex flex-col">
              {renderRow("Format", formatUpper)}
              {renderRow("Size", formatFileSize(basicFormatData.size))}
            </div>
          )}
        </div>

        <div className="flex justify-end border-surface-a10 border-t bg-surface-a10 p-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-surface-a20 bg-surface-a0 px-4 py-2 font-medium text-sm text-text-a0 transition-colors hover:bg-surface-a20"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
