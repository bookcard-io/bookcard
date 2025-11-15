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

import { useCallback, useState } from "react";

export interface UseModalStateReturn<T> {
  /** Whether the modal is open. */
  isOpen: boolean;
  /** Selected item (null for create mode). */
  selectedItem: T | null;
  /** Open modal for creating a new item. */
  openCreate: () => void;
  /** Open modal for editing an existing item. */
  openEdit: (item: T) => void;
  /** Close the modal and clear selected item. */
  close: () => void;
}

/**
 * Hook for managing modal state.
 *
 * Handles modal visibility and selected item state.
 * Follows SRP by focusing solely on modal state management.
 * Follows DRY by centralizing modal state patterns.
 * Follows IOC by providing callbacks for state changes.
 *
 * Parameters
 * ----------
 * T : type
 *     Type of the item being managed in the modal.
 *
 * Returns
 * -------
 * UseModalStateReturn<T>
 *     Object with modal state and handlers.
 */
export function useModalState<T>(): UseModalStateReturn<T> {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<T | null>(null);

  const openCreate = useCallback(() => {
    setSelectedItem(null);
    setIsOpen(true);
  }, []);

  const openEdit = useCallback((item: T) => {
    setSelectedItem(item);
    setIsOpen(true);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    setSelectedItem(null);
  }, []);

  return {
    isOpen,
    selectedItem,
    openCreate,
    openEdit,
    close,
  };
}
