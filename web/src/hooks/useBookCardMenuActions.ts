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

import { useCallback, useMemo } from "react";
import { useUser } from "@/contexts/UserContext";
import { sendBookToDevice } from "@/services/bookService";
import type { Book } from "@/types/book";
import { useDeleteConfirmation } from "./useDeleteConfirmation";

export interface UseBookCardMenuActionsOptions {
  /** Book data. */
  book: Book;
  /** Callback for opening book view. */
  onBookClick?: (book: Book) => void;
  /** Callback when book is deleted successfully. */
  onBookDeleted?: () => void;
  /** Callback when book deletion fails. */
  onDeleteError?: (error: string) => void;
}

export interface UseBookCardMenuActionsResult {
  /** Handler for Book info action. */
  handleBookInfo: () => void;
  /** Handler for Send action. */
  handleSend: () => void;
  /** Handler for Move to library action. */
  handleMoveToLibrary: () => void;
  /** Handler for Convert action. */
  handleConvert: () => void;
  /** Handler for Delete action. */
  handleDelete: () => void;
  /** Handler for More action. */
  handleMore: () => void;
  /** Delete confirmation modal state and controls. */
  deleteConfirmation: ReturnType<typeof useDeleteConfirmation>;
  /** Whether Send action is disabled (no devices available). */
  isSendDisabled: boolean;
}

/**
 * Custom hook for book card menu actions.
 *
 * Provides handlers for all menu actions.
 * Follows SRP by managing only menu action handlers.
 * Uses IOC via callback props.
 *
 * Parameters
 * ----------
 * options : UseBookCardMenuActionsOptions
 *     Configuration including book data and callbacks.
 *
 * Returns
 * -------
 * UseBookCardMenuActionsResult
 *     Menu action handlers.
 */
export function useBookCardMenuActions({
  book,
  onBookClick,
  onBookDeleted,
  onDeleteError,
}: UseBookCardMenuActionsOptions): UseBookCardMenuActionsResult {
  const { user } = useUser();
  const deleteConfirmation = useDeleteConfirmation({
    bookId: book.id,
    onSuccess: () => {
      // Refresh book list or navigate away
      onBookDeleted?.();
    },
    onError: (error) => {
      onDeleteError?.(error);
    },
  });

  // Get device to use: default device, or first device if no default
  const deviceToUse = useMemo(() => {
    if (!user?.ereader_devices || user.ereader_devices.length === 0) {
      return null;
    }
    // Try to find default device
    const defaultDevice = user.ereader_devices.find(
      (device) => device.is_default,
    );
    // Use default if found, otherwise use first device
    return defaultDevice || user.ereader_devices[0] || null;
  }, [user?.ereader_devices]);

  const isSendDisabled = deviceToUse === null;

  const handleBookInfo = useCallback(() => {
    if (onBookClick) {
      onBookClick(book);
    }
  }, [onBookClick, book]);

  const handleSend = useCallback(async () => {
    if (!deviceToUse) {
      return;
    }
    try {
      await sendBookToDevice(book.id, {
        toEmail: deviceToUse.email,
      });
      // Optionally show success message or notification
    } catch (error) {
      console.error("Failed to send book:", error);
      // Optionally show error message or notification
      alert(error instanceof Error ? error.message : "Failed to send book");
    }
  }, [book.id, deviceToUse]);

  const handleMoveToLibrary = useCallback(() => {
    // TODO: Implement move to library functionality
  }, []);

  const handleConvert = useCallback(() => {
    // TODO: Implement convert functionality
  }, []);

  const handleDelete = useCallback(() => {
    deleteConfirmation.open();
  }, [deleteConfirmation]);

  const handleMore = useCallback(() => {
    // TODO: Implement more options functionality
  }, []);

  return {
    handleBookInfo,
    handleSend,
    handleMoveToLibrary,
    handleConvert,
    handleDelete,
    handleMore,
    deleteConfirmation,
    isSendDisabled,
  };
}
