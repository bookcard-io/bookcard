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
import { useAuthorSelection } from "@/hooks/useAuthorSelection";
import { cn } from "@/libs/utils";
import { AuthorMergeModal } from "./AuthorMergeModal";

/**
 * Author merge button component.
 *
 * Shows merge button when authors are selected.
 * Opens merge modal when clicked.
 */
export function AuthorMergeButton() {
  const { selectedCount, selectedAuthorIds } = useAuthorSelection();
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleClick = () => {
    if (selectedCount >= 2) {
      setIsModalOpen(true);
    }
  };

  const handleClose = () => {
    setIsModalOpen(false);
  };

  // Show button when at least 1 author is selected (per requirement)
  // Disable when less than 2 authors selected (validation)
  if (selectedCount === 0) {
    return null;
  }

  return (
    <>
      <button
        type="button"
        onClick={handleClick}
        disabled={selectedCount < 2}
        className={cn(
          "flex items-center gap-2 rounded-md px-4 py-2 font-medium text-sm",
          "transition-colors focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2",
          selectedCount >= 2
            ? "bg-[var(--color-primary-a0)] text-[var(--color-text-primary-a0)] hover:bg-[var(--color-primary-a10)] active:bg-[var(--color-primary-a20)]"
            : "cursor-not-allowed bg-surface-a20 text-text-a40",
        )}
        aria-label={`Merge ${selectedCount} authors`}
      >
        <i className="pi pi-objects-column" aria-hidden="true" />
        <span>Merge authors</span>
        {selectedCount > 0 && (
          <span className="rounded-full bg-white/20 px-2 py-0.5 text-xs">
            {selectedCount}
          </span>
        )}
      </button>
      {isModalOpen && (
        <AuthorMergeModal
          authorIds={Array.from(selectedAuthorIds)}
          onClose={handleClose}
        />
      )}
    </>
  );
}
