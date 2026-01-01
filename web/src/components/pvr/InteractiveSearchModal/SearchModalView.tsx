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

import type { KeyboardEvent, MouseEvent } from "react";
import { FaExclamationCircle, FaSpinner } from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import type { SortDirection } from "@/hooks/pvr/useTableSort";
import { cn } from "@/libs/utils";
import type { SearchResultRead } from "@/types/pvrSearch";
import { SearchResultsTable } from "./SearchResultsTable";

interface SearchModalViewProps {
  onClose: () => void;
  bookTitle: string;
  bookYear?: string;
  isLoading: boolean;
  resultsCount: number;
  error: string | null;
  onRetry: () => void;
  sortedResults: SearchResultRead[];
  sortConfig: { key: string; direction: SortDirection } | null;
  onSort: (key: string) => void;
  onDownload: (index: number) => void;
  downloadingIndex: number | null;
  // Modal interactions
  onOverlayClick: (e: MouseEvent<HTMLDivElement>) => void;
  onOverlayKeyDown: (e: KeyboardEvent<HTMLDivElement>) => void;
  onModalClick: (e: MouseEvent<HTMLDivElement>) => void;
}

export function SearchModalView({
  onClose,
  bookTitle,
  bookYear,
  isLoading,
  resultsCount,
  error,
  onRetry,
  sortedResults,
  sortConfig,
  onSort,
  onDownload,
  downloadingIndex,
  onOverlayClick,
  onOverlayKeyDown,
  onModalClick,
}: SearchModalViewProps) {
  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="modal-overlay modal-overlay-z-1002 modal-overlay-padding"
      onClick={onOverlayClick}
      onKeyDown={onOverlayKeyDown}
      role="presentation"
    >
      <div
        className={cn(
          "modal-container modal-container-shadow-default w-full max-w-6xl flex-col",
          "max-h-[90vh] overflow-hidden",
        )}
        role="dialog"
        aria-modal="true"
        aria-label="Interactive Search"
        onMouseDown={onModalClick}
      >
        <div className="flex items-center justify-between gap-4 border-surface-a20 border-b p-4">
          <h2 className="m-0 truncate font-bold text-text-a0 text-xl">
            Interactive Search - {bookTitle} {bookYear ? `(${bookYear})` : ""}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="modal-close-button modal-close-button-sm focus:outline"
            aria-label="Close"
          >
            <i className="pi pi-times" aria-hidden="true" />
          </button>
        </div>

        <div className="flex-1 overflow-auto bg-surface-tonal-a0 p-4">
          {isLoading && resultsCount === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-text-a30">
              <FaSpinner className="mb-4 animate-spin text-4xl" />
              <p>Searching indexers...</p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-12 text-danger-a10">
              <FaExclamationCircle className="mb-4 text-4xl" />
              <p>{error}</p>
              <Button onClick={onRetry} variant="secondary" className="mt-4">
                Retry Search
              </Button>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              <SearchResultsTable
                results={sortedResults}
                sortConfig={sortConfig}
                onSort={onSort}
                onDownload={onDownload}
                downloadingIndex={downloadingIndex}
              />
            </div>
          )}
        </div>

        <div className="flex justify-between border-surface-a20 border-t bg-surface-a10 p-4">
          <div className="text-sm text-text-a30">{resultsCount} results</div>
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
