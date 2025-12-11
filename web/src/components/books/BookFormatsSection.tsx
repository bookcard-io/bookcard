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

import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { AddFormatButton } from "@/components/books/AddFormatButton";
import { ConversionModal } from "@/components/books/ConversionModal";
import { FormatInfoModal } from "@/components/books/FormatInfoModal";
import { FormatList } from "@/components/books/FormatList";
import { IconButton } from "@/components/books/IconButton";
import { ReplaceFormatConfirmationModal } from "@/components/books/ReplaceFormatConfirmationModal";
import { Button } from "@/components/forms/Button";
import { useUser } from "@/contexts/UserContext";
import { useFormatUpload } from "@/hooks/useFormatUpload";
import type { Book } from "@/types/book";
import { getFileExtension } from "@/utils/format";
import { buildBookPermissionContext } from "@/utils/permissions";

export interface BookFormatsSectionProps {
  /** Book data containing formats. */
  book: Book;
  /** Optional callback when format is added (for IoC). */
  onFormatAdded?: () => void;
}

/**
 * Book formats section component.
 *
 * Displays book file formats and format actions.
 * Follows SRP by delegating to specialized components and hooks.
 * Follows SOC by separating presentation from business logic.
 * Follows IoC by accepting optional callbacks for extensibility.
 *
 * Parameters
 * ----------
 * props : BookFormatsSectionProps
 *     Component props including book data and optional callbacks.
 */
export function BookFormatsSection({
  book,
  onFormatAdded,
}: BookFormatsSectionProps) {
  const router = useRouter();
  const { canPerformAction } = useUser();
  const bookContext = buildBookPermissionContext(book);
  const canWrite = canPerformAction("books", "write", bookContext);
  const canDelete = canPerformAction("books", "delete", bookContext);
  const [isConversionModalOpen, setIsConversionModalOpen] = useState(false);
  const [selectedFormatForInfo, setSelectedFormatForInfo] = useState<{
    format: string;
    size: number;
  } | null>(null);

  const [localFormats, setLocalFormats] = useState(book.formats || []);

  const handleFormatAdded = useCallback(() => {
    router.refresh();
    // Re-fetch logic or manual update would be better here, but for now relying on router.refresh()
    // However, user reports UI not updating.
    // Let's manually fetch the book to get updated formats
    fetch(`/api/books/${book.id}?full=true`)
      .then((res) => res.json())
      .then((data) => {
        if (data.formats) {
          setLocalFormats(data.formats);
        }
      })
      .catch((err) => console.error("Failed to refresh book formats", err));

    onFormatAdded?.();
  }, [book.id, router, onFormatAdded]);

  const {
    isUploading,
    showReplaceModal,
    pendingFile,
    upload,
    confirmReplace,
    cancelReplace,
    error,
  } = useFormatUpload({
    bookId: book.id,
    onSuccess: handleFormatAdded,
  });

  const openConversionModal = useCallback(
    () => setIsConversionModalOpen(true),
    [],
  );
  const closeConversionModal = useCallback(
    () => setIsConversionModalOpen(false),
    [],
  );

  const handleFileChange = useCallback(
    (file: File) => {
      void upload(file, false);
    },
    [upload],
  );

  const handleDeleteFormat = useCallback(
    async (format: string) => {
      try {
        const response = await fetch(
          `/api/books/${book.id}/formats/${format}`,
          {
            method: "DELETE",
          },
        );

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || "Failed to delete format");
        }

        // Manually update local state to remove the deleted format immediately
        setLocalFormats((prev) => prev.filter((f) => f.format !== format));

        router.refresh();
        onFormatAdded?.();
      } catch (error) {
        console.error("Failed to delete format", error);
        // TODO: Show toast error
      }
    },
    [book.id, router, onFormatAdded],
  );

  const isLastFormat = localFormats.length <= 1;

  const renderFormatActions = useCallback(
    (format: { format: string; size: number }) => (
      <>
        <IconButton
          icon="pi-info-circle"
          label={`Info for ${format.format.toUpperCase()}`}
          onClick={() => setSelectedFormatForInfo(format)}
        />
        <IconButton
          icon="pi-copy"
          label={`Copy ${format.format.toUpperCase()}`}
          disabled={!canWrite}
        />
        <IconButton
          icon="pi-trash"
          label={`Delete ${format.format.toUpperCase()}`}
          disabled={!canDelete || isLastFormat}
          onClick={() => {
            void handleDeleteFormat(format.format);
          }}
        />
      </>
    ),
    [canWrite, canDelete, isLastFormat, handleDeleteFormat],
  );

  return (
    <div className="mt-6 flex flex-col gap-4">
      <h3 className="m-0 font-bold text-text-a0 text-xl">Formats</h3>
      {error && (
        <div className="rounded-md border border-error-a20 bg-error-a10 p-3 text-error-a0 text-sm">
          {error}
        </div>
      )}
      <FormatList formats={localFormats} renderActions={renderFormatActions} />
      <div className="flex flex-col gap-2">
        <AddFormatButton
          disabled={!canWrite}
          isUploading={isUploading}
          onFileChange={handleFileChange}
        />
        <Button
          type="button"
          variant="ghost"
          size="small"
          disabled={!canWrite}
          onClick={openConversionModal}
          className="!border-primary-a20 !text-primary-a20 hover:!text-primary-a20 w-full justify-start rounded-md hover:border-primary-a10 hover:bg-surface-a20 focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <span
            className="pi pi-arrow-right-arrow-left mr-2 text-primary-a20"
            aria-hidden="true"
          />
          Convert
        </Button>
      </div>
      <ConversionModal
        book={book}
        isOpen={isConversionModalOpen}
        onClose={closeConversionModal}
      />
      <FormatInfoModal
        isOpen={!!selectedFormatForInfo}
        onClose={() => setSelectedFormatForInfo(null)}
        format={selectedFormatForInfo || { format: "", size: 0 }}
        bookId={book.id}
        bookTitle={book.title}
      />
      <ReplaceFormatConfirmationModal
        isOpen={showReplaceModal}
        onClose={cancelReplace}
        onConfirm={confirmReplace}
        format={pendingFile ? getFileExtension(pendingFile.name) : ""}
        isReplacing={isUploading}
      />
    </div>
  );
}
