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

import { Button } from "@/components/forms/Button";
import { AddBookForm } from "@/components/tracked-books/AddBookForm";
import { BookPreview } from "@/components/tracked-books/BookPreview";
import { useAddBookForm } from "@/hooks/useAddBookForm";
import { useModal } from "@/hooks/useModal";
import type { MetadataSearchResult, MonitorMode } from "@/types/trackedBook";

export interface AddBookModalProps {
  isOpen: boolean;
  book: MetadataSearchResult | null;
  onClose: () => void;
  onAdd: (
    book: MetadataSearchResult,
    settings: {
      libraryId?: number;
      monitor: MonitorMode;
      monitorValue: string;
      preferredFormats: string[];
      tags: string[];
    },
  ) => Promise<void>;
  isAdding?: boolean;
}

export function AddBookModal({
  isOpen,
  book,
  onClose,
  onAdd,
  isAdding = false,
}: AddBookModalProps) {
  const {
    formState,
    setLibraryId,
    setMonitor,
    setMonitorValue,
    setTags,
    currentFormatMode,
    handleFormatModeChange,
    libraries,
  } = useAddBookForm(book, isOpen);

  useModal(isOpen);

  if (!isOpen || !book) return null;

  const handleSubmit = async () => {
    try {
      await onAdd(book, formState);
      onClose();
    } catch (error) {
      console.error("Failed to add book:", error);
    }
  };

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="modal-overlay modal-overlay-z-1000 modal-overlay-padding-responsive"
      onClick={(e) => e.target === e.currentTarget && onClose()}
      onKeyDown={(e) => {
        if (e.key === "Escape") onClose();
        if (e.key === "Enter" || e.key === " ") {
          if (e.target === e.currentTarget) onClose();
        }
      }}
    >
      <div
        className="modal-container modal-container-shadow-large w-full max-w-5xl md:rounded-md"
        role="dialog"
        aria-modal="true"
        aria-label="Add Book"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-surface-a20 border-b p-4 md:p-6">
          <h2 className="font-bold text-text-a0 text-xl">Add New Book</h2>
          <button
            type="button"
            onClick={onClose}
            className="text-text-a30 transition-colors hover:text-text-a0"
          >
            <i className="pi pi-times text-xl" />
          </button>
        </div>

        {/* Content */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
          className="flex flex-col gap-6 p-4 md:flex-row md:p-6"
        >
          <BookPreview book={book}>
            <AddBookForm
              libraryId={formState.libraryId}
              currentFormatMode={currentFormatMode}
              monitor={formState.monitor}
              monitorValue={formState.monitorValue}
              tags={formState.tags}
              libraries={libraries}
              onLibraryChange={setLibraryId}
              onFormatModeChange={handleFormatModeChange}
              onMonitorChange={setMonitor}
              onMonitorValueChange={setMonitorValue}
              onTagsChange={setTags}
            />
          </BookPreview>
        </form>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 border-surface-a20 border-t bg-surface-tonal-a10 p-4">
          <Button variant="ghost" onClick={onClose} disabled={isAdding}>
            Cancel
          </Button>
          <Button loading={isAdding} onClick={handleSubmit}>
            Add book
          </Button>
        </div>
      </div>
    </div>
  );
}
