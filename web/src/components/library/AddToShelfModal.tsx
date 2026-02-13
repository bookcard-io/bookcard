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

import { useCallback, useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { Button } from "@/components/forms/Button";
import { TextInput } from "@/components/forms/TextInput";
import { ShelfEditModal } from "@/components/shelves/ShelfEditModal";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { useSelectedBooks } from "@/contexts/SelectedBooksContext";
import { useShelvesContext } from "@/contexts/ShelvesContext";
import { useUser } from "@/contexts/UserContext";
import { useBook } from "@/hooks/useBook";
import { useModal } from "@/hooks/useModal";
import { useShelfActions } from "@/hooks/useShelfActions";
import { useShelves } from "@/hooks/useShelves";
import { InterfaceContentBook2LibraryContentBooksBookShelfStack } from "@/icons/Shelf";
import { cn } from "@/libs/utils";
import type { CreateShelfOptions } from "@/services/shelfService";
import type { Book } from "@/types/book";
import type { Shelf, ShelfCreate, ShelfUpdate } from "@/types/shelf";
import { buildShelfCreatePayload } from "@/utils/shelfPayload";
import { isMagicShelf } from "@/utils/shelfUtils";
import { getShelfCoverUrlWithCacheBuster } from "@/utils/shelves";

export interface AddToShelfModalProps {
  /** Books to add to shelf. If not provided, uses selected books from context. */
  books?: Book[];
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when books are successfully added to shelf (to close parent menu). */
  onSuccess?: () => void;
}

/**
 * Modal for adding a book to a shelf (Plex-style).
 *
 * Displays a list of shelves with cover pictures in a table format.
 * Allows selecting an existing shelf or creating a new one.
 * Follows SRP by focusing solely on shelf selection and creation.
 * Uses IOC via hooks and callback props.
 */
export function AddToShelfModal({
  books: booksProp,
  onClose,
  onSuccess,
}: AddToShelfModalProps) {
  const { canPerformAction } = useUser();
  const { showDanger } = useGlobalMessages();
  const canEditShelves = canPerformAction("shelves", "edit");
  const canCreateShelves = canPerformAction("shelves", "create");

  // Get books from context if not provided via prop
  const { selectedBookIds, books: contextBooks } = useSelectedBooks();
  const books = useMemo(() => {
    if (booksProp) {
      return booksProp;
    }
    // Use selected books from context
    if (selectedBookIds.size === 0 || contextBooks.length === 0) {
      return [];
    }
    return contextBooks.filter((book) => selectedBookIds.has(book.id));
  }, [booksProp, selectedBookIds, contextBooks]);

  // Get first book for cover and title (for automatic shelf naming)
  const firstBook = books[0];
  const { book, isLoading: isBookLoading } = useBook({
    bookId: firstBook?.id ?? 0,
    enabled: books.length > 0 && firstBook !== undefined,
    full: false,
  });

  const { shelves, refresh: refreshShelvesContext } = useShelvesContext();
  const { addBook, isProcessing } = useShelfActions();
  const { createShelf } = useShelves();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newShelfName, setNewShelfName] = useState("");
  const [initialCoverFile, setInitialCoverFile] = useState<File | null>(null);

  // Prevent body scroll when modal is open
  useModal(true);

  // Sort shelves by created_at descending (newest first)
  const sortedShelves = useMemo(() => {
    return [...shelves]
      .filter((shelf) => !isMagicShelf(shelf))
      .sort((a, b) => {
        const dateA = new Date(a.created_at).getTime();
        const dateB = new Date(b.created_at).getTime();
        return dateB - dateA; // Descending order
      });
  }, [shelves]);

  // Get first book title for input field (for automatic shelf naming)
  const bookTitle = firstBook?.title || book?.title || "";

  // Initialize new shelf name with first book title when available
  useEffect(() => {
    if (bookTitle && !newShelfName) {
      setNewShelfName(bookTitle);
    }
  }, [bookTitle, newShelfName]);

  // Fetch first book cover and convert to File when book loads
  useEffect(() => {
    const fetchBookCover = async () => {
      if (!book?.thumbnail_url || !book?.has_cover || !firstBook) {
        setInitialCoverFile(null);
        return;
      }

      try {
        // Fetch the cover image
        const response = await fetch(book.thumbnail_url, {
          credentials: "include",
        });
        if (!response.ok) {
          setInitialCoverFile(null);
          return;
        }

        // Convert to blob
        const blob = await response.blob();
        // Determine file extension from content type or default to jpg
        const contentType = blob.type || "image/jpeg";
        const extension = contentType.split("/")[1] || "jpg";
        const fileName = `book-cover-${firstBook.id}.${extension}`;

        // Convert blob to File
        const file = new File([blob], fileName, {
          type: contentType,
          lastModified: Date.now(),
        });

        setInitialCoverFile(file);
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Failed to fetch book cover";
        showDanger(errorMessage);
        setInitialCoverFile(null);
      }
    };

    void fetchBookCover();
  }, [book?.thumbnail_url, book?.has_cover, firstBook, showDanger]);

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) {
        onClose();
      }
    },
    [onClose],
  );

  const handleOverlayKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Escape") {
        onClose();
      }
    },
    [onClose],
  );

  const handleModalClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      e.stopPropagation();
    },
    [],
  );

  /**
   * Handle selecting an existing shelf.
   *
   * Adds all books to the shelf. If any book is already in the shelf,
   * it's skipped (no-op). Only shows error if all books fail.
   */
  const handleShelfSelect = useCallback(
    async (shelfId: number) => {
      if (!canEditShelves || books.length === 0) {
        return;
      }

      const results = await Promise.allSettled(
        books
          .filter(
            (b): b is typeof b & { library_id: number } => b.library_id != null,
          )
          .map((book) => addBook(shelfId, book.id, book.library_id)),
      );

      const failed = results.filter((r) => r.status === "rejected").length;

      // Check if all failures are due to books already being in shelf
      const allAlreadyInShelf = results
        .filter((r) => r.status === "rejected")
        .every((r) => {
          const errorMessage =
            r.reason instanceof Error ? r.reason.message : String(r.reason);
          return (
            errorMessage.toLowerCase().includes("already in shelf") ||
            errorMessage.toLowerCase().includes("already exists")
          );
        });

      // If all books are already in shelf or all succeeded, treat as success
      if (failed === 0 || allAlreadyInShelf) {
        await refreshShelvesContext();
        onClose();
        onSuccess?.();
        return;
      }

      // If some books failed for other reasons, show error but still close modal
      // (some books may have been added successfully)
      if (failed > 0) {
        const errorMessages = results
          .filter((r) => r.status === "rejected")
          .map((r) => {
            const errorMessage =
              r.reason instanceof Error
                ? r.reason.message
                : "Failed to add book";
            return errorMessage;
          });
        const uniqueErrors = [...new Set(errorMessages)];
        showDanger(uniqueErrors[0] || "Failed to add some books to shelf");
      }

      // Refresh shelves context and close modal
      await refreshShelvesContext();
      onClose();
      onSuccess?.();
    },
    [
      canEditShelves,
      books,
      addBook,
      refreshShelvesContext,
      onClose,
      onSuccess,
      showDanger,
    ],
  );

  /**
   * Handle creating a new shelf.
   * The shelf name from the input field is passed to ShelfEditModal,
   * which will use it as the initial name.
   * Automatically adds all books to the newly created shelf.
   */
  const handleCreateShelf = useCallback(
    async (
      data: ShelfCreate | ShelfUpdate,
      options?: CreateShelfOptions,
    ): Promise<Shelf> => {
      const shelfData = buildShelfCreatePayload(data, {
        fallbackName: newShelfName,
      });
      const newShelf = await createShelf(shelfData, options);

      // Automatically add all books to the newly created shelf
      const booksWithLibrary = books.filter(
        (b): b is typeof b & { library_id: number } => b.library_id != null,
      );
      if (booksWithLibrary.length > 0) {
        const results = await Promise.allSettled(
          booksWithLibrary.map((book) =>
            addBook(newShelf.id, book.id, book.library_id),
          ),
        );

        const failed = results.filter((r) => r.status === "rejected").length;

        if (failed > 0) {
          const errorMessages = results
            .filter((r) => r.status === "rejected")
            .map((r) => {
              const errorMessage =
                r.reason instanceof Error
                  ? r.reason.message
                  : "Failed to add book to new shelf";
              return errorMessage;
            });
          const uniqueErrors = [...new Set(errorMessages)];
          showDanger(
            uniqueErrors[0] || "Failed to add some books to new shelf",
          );
        }
      }

      await refreshShelvesContext();
      onClose();
      onSuccess?.();
      return newShelf;
    },
    [
      createShelf,
      refreshShelvesContext,
      addBook,
      books,
      onClose,
      onSuccess,
      newShelfName,
      showDanger,
    ],
  );

  /**
   * Handle create button click.
   */
  const handleCreateClick = useCallback(() => {
    if (newShelfName.trim() && canCreateShelves) {
      setShowCreateModal(true);
    }
  }, [newShelfName, canCreateShelves]);

  const modalContent = (
    <>
      {/* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */}
      <div
        className="modal-overlay modal-overlay-z-50 modal-overlay-padding"
        onClick={handleOverlayClick}
        onKeyDown={handleOverlayKeyDown}
        role="presentation"
        data-keep-selection
      >
        <div
          className="modal-container modal-container-shadow-default mx-auto my-auto max-h-[90vh] w-full max-w-lg flex-col overflow-hidden"
          role="dialog"
          aria-modal="true"
          aria-label="Add to shelf"
          onMouseDown={handleModalClick}
          data-keep-selection
        >
          {/* Header */}
          <div className="flex items-center justify-between border-surface-a20 border-b px-6 py-4">
            <h2 className="m-0 font-bold text-text-a0 text-xl leading-[1.4]">
              Add to shelf
            </h2>
            <button
              type="button"
              onClick={onClose}
              className="modal-close-button modal-close-button-sm h-8 w-8 focus:outline"
              aria-label="Close"
            >
              <i className="pi pi-times" aria-hidden="true" />
            </button>
          </div>

          {/* Main content: Shelf list */}
          <div className="flex-1 overflow-y-auto">
            <table className="w-full border-collapse">
              <tbody>
                {sortedShelves.map((shelf, index) => (
                  <tr
                    key={shelf.id}
                    className={cn(
                      "transition-colors duration-150",
                      canEditShelves && "cursor-pointer",
                      index % 2 === 0
                        ? "bg-surface-tonal-a0"
                        : "bg-surface-tonal-a10",
                      canEditShelves && "hover:bg-surface-tonal-a20",
                      !canEditShelves && "cursor-not-allowed opacity-50",
                    )}
                    onClick={
                      canEditShelves
                        ? () => handleShelfSelect(shelf.id)
                        : undefined
                    }
                  >
                    <td className="px-4 py-3 align-middle">
                      <div className="flex items-center gap-3">
                        {/* Shelf cover thumbnail */}
                        <div className="relative h-12 w-12 flex-shrink-0 overflow-hidden rounded">
                          {shelf.cover_picture ? (
                            <ImageWithLoading
                              src={getShelfCoverUrlWithCacheBuster(shelf.id)}
                              alt={`${shelf.name} cover`}
                              width={48}
                              height={48}
                              className="h-full w-full object-cover"
                              containerClassName="w-full h-full"
                              unoptimized
                            />
                          ) : (
                            <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-surface-a20 to-surface-a10">
                              <InterfaceContentBook2LibraryContentBooksBookShelfStack className="h-6 w-6 text-text-a40" />
                            </div>
                          )}
                        </div>
                        {/* Shelf name */}
                        <span className="text-base text-text-a0">
                          {shelf.name}
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Footer */}
          <div className="flex items-center gap-3 border-surface-a20 border-t px-6 py-4">
            <TextInput
              id="new-shelf-name"
              label=""
              value={newShelfName}
              onChange={(e) => setNewShelfName(e.target.value)}
              placeholder={
                isBookLoading ? "Loading..." : bookTitle || "Shelf name"
              }
              className="flex-1"
              disabled={!canCreateShelves}
              onKeyDown={(e) => {
                if (
                  e.key === "Enter" &&
                  newShelfName.trim() &&
                  canCreateShelves
                ) {
                  e.preventDefault();
                  handleCreateClick();
                }
              }}
            />
            <Button
              type="button"
              variant="primary"
              size="medium"
              onClick={handleCreateClick}
              disabled={
                !canCreateShelves || !newShelfName.trim() || isProcessing
              }
            >
              Create
            </Button>
          </div>
        </div>
      </div>

      {/* Create shelf modal */}
      {showCreateModal && (
        <ShelfEditModal
          shelf={null}
          initialName={newShelfName.trim()}
          initialCoverFile={initialCoverFile}
          onClose={() => setShowCreateModal(false)}
          onSave={handleCreateShelf}
          onCoverSaved={async () => {
            // Ensure shelves context reflects the new cover immediately
            await refreshShelvesContext();
          }}
          onCoverDeleted={async () => {
            await refreshShelvesContext();
          }}
        />
      )}
    </>
  );

  // Render modal in a portal to ensure consistent positioning
  return createPortal(modalContent, document.body);
}
