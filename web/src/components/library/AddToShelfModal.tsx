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
import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { Button } from "@/components/forms/Button";
import { TextInput } from "@/components/forms/TextInput";
import { ShelfEditModal } from "@/components/shelves/ShelfEditModal";
import { useShelvesContext } from "@/contexts/ShelvesContext";
import { useBook } from "@/hooks/useBook";
import { useModal } from "@/hooks/useModal";
import { useShelfActions } from "@/hooks/useShelfActions";
import { useShelves } from "@/hooks/useShelves";
import { InterfaceContentBook2LibraryContentBooksBookShelfStack } from "@/icons/Shelf";
import { cn } from "@/libs/utils";
import type { Shelf, ShelfCreate, ShelfUpdate } from "@/types/shelf";
import { getShelfCoverUrlWithCacheBuster } from "@/utils/shelves";

export interface AddToShelfModalProps {
  /** Book ID to add to shelf. */
  bookId: number;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when book is successfully added to shelf (to close parent menu). */
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
  bookId,
  onClose,
  onSuccess,
}: AddToShelfModalProps) {
  const { book, isLoading: isBookLoading } = useBook({
    bookId,
    enabled: true,
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
    return [...shelves].sort((a, b) => {
      const dateA = new Date(a.created_at).getTime();
      const dateB = new Date(b.created_at).getTime();
      return dateB - dateA; // Descending order
    });
  }, [shelves]);

  // Get book title for input field
  const bookTitle = book?.title || "";

  // Initialize new shelf name with book title when book loads
  useEffect(() => {
    if (bookTitle && !newShelfName) {
      setNewShelfName(bookTitle);
    }
  }, [bookTitle, newShelfName]);

  // Fetch book cover and convert to File when book loads
  useEffect(() => {
    const fetchBookCover = async () => {
      if (!book?.thumbnail_url || !book?.has_cover) {
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
        const fileName = `book-cover-${bookId}.${extension}`;

        // Convert blob to File
        const file = new File([blob], fileName, {
          type: contentType,
          lastModified: Date.now(),
        });

        setInitialCoverFile(file);
      } catch (error) {
        console.error("Failed to fetch book cover:", error);
        setInitialCoverFile(null);
      }
    };

    void fetchBookCover();
  }, [book?.thumbnail_url, book?.has_cover, bookId]);

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
   */
  const handleShelfSelect = useCallback(
    async (shelfId: number) => {
      try {
        await addBook(shelfId, bookId);
        await refreshShelvesContext();
        onClose();
        onSuccess?.();
      } catch (error) {
        // If book is already in shelf, treat as success (no-op) and close modal
        const errorMessage =
          error instanceof Error ? error.message : String(error);
        if (
          errorMessage.toLowerCase().includes("already in shelf") ||
          errorMessage.toLowerCase().includes("already exists")
        ) {
          // Silently no-op and close modal
          onClose();
          onSuccess?.();
          return;
        }
        // For other errors, log but don't close modal
        console.error("Failed to add book to shelf:", error);
      }
    },
    [addBook, bookId, refreshShelvesContext, onClose, onSuccess],
  );

  /**
   * Handle creating a new shelf.
   * The shelf name from the input field is passed to ShelfEditModal,
   * which will use it as the initial name.
   */
  const handleCreateShelf = useCallback(
    async (data: ShelfCreate | ShelfUpdate): Promise<Shelf> => {
      // If no name is provided in data, use the input field value
      const shelfData: ShelfCreate = {
        name: data.name || newShelfName.trim() || "",
        description: data.description || null,
        is_public: data.is_public || false,
      };
      const newShelf = await createShelf(shelfData);
      // Automatically add book to the newly created shelf
      try {
        await addBook(newShelf.id, bookId);
        await refreshShelvesContext();
        onClose();
        onSuccess?.();
      } catch (error) {
        console.error("Failed to add book to new shelf:", error);
        // Still close modal even if adding fails
        onClose();
        onSuccess?.();
      }
      return newShelf;
    },
    [
      createShelf,
      refreshShelvesContext,
      addBook,
      bookId,
      onClose,
      onSuccess,
      newShelfName,
    ],
  );

  /**
   * Handle create button click.
   */
  const handleCreateClick = useCallback(() => {
    if (newShelfName.trim()) {
      setShowCreateModal(true);
    }
  }, [newShelfName]);

  return (
    <>
      {/* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */}
      <div
        className="fixed inset-0 z-50 flex animate-[fadeIn_0.2s_ease-out] items-center justify-center overflow-y-auto bg-black/70 p-4"
        onClick={handleOverlayClick}
        onKeyDown={handleOverlayKeyDown}
        role="presentation"
      >
        <div
          className="relative flex h-[480px] w-[528px] animate-[slideUp_0.3s_ease-out] flex-col overflow-hidden rounded-2xl bg-surface-a10 shadow-[var(--shadow-card-hover)]"
          role="dialog"
          aria-modal="true"
          aria-label="Add to shelf"
          onMouseDown={handleModalClick}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-surface-a20 border-b px-6 py-4">
            <h2 className="m-0 font-bold text-text-a0 text-xl leading-[1.4]">
              Add to shelf
            </h2>
            <button
              type="button"
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-full border-none bg-transparent p-0 text-2xl text-text-a30 leading-none transition-colors duration-200 hover:bg-surface-a20 hover:text-text-a0 focus:outline focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2"
              aria-label="Close"
            >
              ×
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
                      "cursor-pointer transition-colors duration-150",
                      index % 2 === 0
                        ? "bg-surface-tonal-a0"
                        : "bg-surface-tonal-a10",
                      "hover:bg-surface-tonal-a20",
                    )}
                    onClick={() => handleShelfSelect(shelf.id)}
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
              onKeyDown={(e) => {
                if (e.key === "Enter" && newShelfName.trim()) {
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
              disabled={!newShelfName.trim() || isProcessing}
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
}
