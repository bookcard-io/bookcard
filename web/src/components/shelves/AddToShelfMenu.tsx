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

import { useState } from "react";
import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";
import { useShelfActions } from "@/hooks/useShelfActions";
import { useShelves } from "@/hooks/useShelves";

export interface AddToShelfMenuItemsProps {
  /** Book ID to add to shelf. */
  bookId: number;
  /** Callback when book is added to a shelf. */
  onAdded?: () => void;
  /** Callback when menu item is clicked (to close menu). */
  onItemClick?: () => void;
}

/**
 * Add to shelf menu items component.
 *
 * Renders dropdown menu items for available shelves to add a book to.
 * This component should be used within a DropdownMenu component.
 */
export function AddToShelfMenuItems({
  bookId,
  onAdded,
  onItemClick,
}: AddToShelfMenuItemsProps) {
  const { shelves, isLoading } = useShelves();
  const { addBook, isProcessing } = useShelfActions();
  const [error, setError] = useState<string | null>(null);

  const handleAddToShelf = async (shelfId: number) => {
    setError(null);
    try {
      await addBook(shelfId, bookId);
      if (onAdded) {
        onAdded();
      }
      if (onItemClick) {
        onItemClick();
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to add book to shelf",
      );
    }
  };

  if (isLoading) {
    return <DropdownMenuItem label="Loading shelves..." disabled />;
  }

  if (shelves.length === 0) {
    return <DropdownMenuItem label="No shelves available" disabled />;
  }

  return (
    <>
      {shelves.map((shelf) => (
        <DropdownMenuItem
          key={shelf.id}
          label={`${shelf.name}${shelf.is_public ? " (Public)" : ""}`}
          onClick={() => handleAddToShelf(shelf.id)}
          disabled={isProcessing}
        />
      ))}
      {error && <div className="px-4 py-2 text-red-600 text-sm">{error}</div>}
    </>
  );
}
