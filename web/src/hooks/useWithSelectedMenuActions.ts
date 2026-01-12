// Copyright (C) 2026 knguyen and others
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

import { useCallback, useMemo, useState } from "react";
import { useUser } from "@/contexts/UserContext";
import { queueBooksToDevice } from "@/services/bookService";
import type { Book } from "@/types/book";

export interface UseWithSelectedMenuActionsOptions {
  /** Selected books. */
  selectedBooks: Book[];
  /** Callback fired when actions complete successfully. */
  onSuccess?: () => void;
  /** Callback fired when actions fail. */
  onError?: (error: string) => void;
}

export interface UseWithSelectedMenuActionsResult {
  /** Handler for Batch edit action. */
  onBatchEdit: () => void;
  /** Handler for Move to library action. */
  onMoveToLibrary: () => void;
  /** Handler for Convert action. */
  onConvert: () => void;
  /** Handler for Delete action. */
  onDelete: () => void;
  /** Handler for Merge action. */
  onMerge: () => void;
  /** Handler for Send action. */
  onSend: () => void;
  /** Handler for Add to shelf action. */
  onAddToShelf: () => void;
  /** Add to shelf modal state and controls. */
  addToShelfState: {
    isOpen: boolean;
    open: () => void;
    close: () => void;
  };
  /** Whether Send action is disabled. */
  isSendDisabled: boolean;
}

/**
 * Custom hook for "With selected" menu actions.
 *
 * Provides handlers for all menu actions.
 * Follows SRP by managing only menu action handlers.
 * Uses IOC via callback props.
 *
 * Parameters
 * ----------
 * options : UseWithSelectedMenuActionsOptions
 *     Configuration including selected books and callbacks.
 *
 * Returns
 * -------
 * UseWithSelectedMenuActionsResult
 *     Menu action handlers.
 */
export function useWithSelectedMenuActions({
  selectedBooks,
  onSuccess,
  onError,
}: UseWithSelectedMenuActionsOptions): UseWithSelectedMenuActionsResult {
  const { user } = useUser();
  const [showAddToShelfModal, setShowAddToShelfModal] = useState(false);

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

  const onBatchEdit = useCallback(() => {
    // TODO: Implement batch edit
    console.log("Batch edit", selectedBooks);
  }, [selectedBooks]);

  const onMoveToLibrary = useCallback(() => {
    // TODO: Implement move to library
    console.log("Move to library", selectedBooks);
  }, [selectedBooks]);

  const onConvert = useCallback(() => {
    // TODO: Implement convert
    console.log("Convert", selectedBooks);
  }, [selectedBooks]);

  const onDelete = useCallback(() => {
    // TODO: Implement delete
    console.log("Delete", selectedBooks);
  }, [selectedBooks]);

  const onMerge = useCallback(() => {
    // TODO: Implement merge
    console.log("Merge", selectedBooks);
  }, [selectedBooks]);

  const onSend = useCallback(async () => {
    if (!deviceToUse) {
      return;
    }
    try {
      const bookIds = selectedBooks.map((b) => b.id);
      await queueBooksToDevice(bookIds, {
        toEmail: deviceToUse.email,
      });
      onSuccess?.();
    } catch (error) {
      console.error("Failed to send books:", error);
      onError?.(
        error instanceof Error ? error.message : "Failed to send books",
      );
    }
  }, [selectedBooks, deviceToUse, onSuccess, onError]);

  const onAddToShelf = useCallback(() => {
    setShowAddToShelfModal(true);
  }, []);

  const closeAddToShelfModal = useCallback(() => {
    setShowAddToShelfModal(false);
  }, []);

  return {
    onBatchEdit,
    onMoveToLibrary,
    onConvert,
    onDelete,
    onMerge,
    onSend,
    onAddToShelf,
    addToShelfState: {
      isOpen: showAddToShelfModal,
      open: onAddToShelf,
      close: closeAddToShelfModal,
    },
    isSendDisabled,
  };
}
