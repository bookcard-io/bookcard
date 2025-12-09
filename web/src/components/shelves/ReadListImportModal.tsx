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

import { useCallback, useState } from "react";
import { Button } from "@/components/forms/Button";
import { useModal } from "@/hooks/useModal";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import { importReadList } from "@/services/shelfService";
import type { ImportResult, Shelf } from "@/types/shelf";

export interface ReadListImportModalProps {
  /** Shelf to import into. */
  shelf: Shelf;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when import completes successfully. */
  onImportComplete?: (result: ImportResult) => void;
}

/**
 * Modal component for importing read lists from files.
 *
 * Allows users to upload ComicRack .cbl files and import them
 * into a shelf as a read list.
 */
export function ReadListImportModal({
  shelf,
  onClose,
  onImportComplete,
}: ReadListImportModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useModal(true);
  const { handleOverlayClick, handleModalClick } = useModalInteractions({
    onClose,
  });

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0];
      if (selectedFile) {
        setFile(selectedFile);
        setError(null);
        setImportResult(null);
      }
    },
    [],
  );

  const handleImport = useCallback(async () => {
    if (!file) {
      setError("Please select a file to import");
      return;
    }

    setIsImporting(true);
    setError(null);

    try {
      const result = await importReadList(
        shelf.id,
        { importer: "comicrack", auto_add_matched: false },
        file,
      );
      setImportResult(result);
      if (onImportComplete) {
        onImportComplete(result);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setIsImporting(false);
    }
  }, [file, shelf.id, onImportComplete]);

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="modal-overlay modal-overlay-z-50 modal-overlay-padding"
      onClick={handleOverlayClick}
      role="presentation"
    >
      <div
        className="modal-container modal-container-shadow-default w-full max-w-2xl flex-col"
        role="dialog"
        aria-modal="true"
        aria-label="Import read list"
        onMouseDown={handleModalClick}
      >
        <button
          type="button"
          onClick={onClose}
          className="modal-close-button modal-close-button-sm focus:outline"
          aria-label="Close"
        >
          <i className="pi pi-times" aria-hidden="true" />
        </button>

        <div className="flex items-start justify-between gap-4 border-surface-a20 border-b pt-6 pr-16 pb-4 pl-6">
          <h2 className="m-0 truncate font-bold text-2xl text-text-a0 leading-[1.4]">
            Import Read List
          </h2>
        </div>

        <div className="flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto p-6">
          <div className="flex flex-col gap-2">
            <label
              htmlFor="readlist-file-input"
              className="font-medium text-sm text-text-a0"
            >
              Select file (.cbl)
            </label>
            <input
              id="readlist-file-input"
              type="file"
              accept=".cbl"
              onChange={handleFileChange}
              className="text-sm"
              disabled={isImporting}
            />
          </div>

          {error && (
            <div
              className="rounded-md bg-danger-a20 px-4 py-3 text-danger-a0 text-sm"
              role="alert"
            >
              {error}
            </div>
          )}

          {importResult && (
            <div className="flex flex-col gap-4">
              <div className="rounded-md bg-success-a20 px-4 py-3 text-sm text-success-a0">
                Import completed: {importResult.matched.length} matched,{" "}
                {importResult.unmatched.length} unmatched
              </div>
              {importResult.matched.length > 0 && (
                <div>
                  <h3 className="font-medium text-sm text-text-a0">
                    Matched Books ({importResult.matched.length})
                  </h3>
                  <ul className="mt-2 max-h-40 overflow-y-auto text-sm">
                    {importResult.matched.map((match) => (
                      <li key={match.book_id} className="py-1">
                        Book ID {match.book_id} ({match.match_type}, confidence:{" "}
                        {(match.confidence * 100).toFixed(0)}%)
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {importResult.unmatched.length > 0 && (
                <div>
                  <h3 className="font-medium text-sm text-text-a0">
                    Unmatched Books ({importResult.unmatched.length})
                  </h3>
                  <ul className="mt-2 max-h-40 overflow-y-auto text-sm">
                    {importResult.unmatched.map((ref, idx) => (
                      <li
                        key={`${ref.series}-${ref.title}-${ref.year}-${idx}`}
                        className="py-1"
                      >
                        {ref.series || ref.title || "Unknown"}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          <div className="flex justify-end gap-2 border-surface-a20 border-t pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={onClose}
              disabled={isImporting}
            >
              Close
            </Button>
            <Button
              type="button"
              variant="primary"
              onClick={handleImport}
              disabled={!file || isImporting}
            >
              {isImporting ? "Importing..." : "Import"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
