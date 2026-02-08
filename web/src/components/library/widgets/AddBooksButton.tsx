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

import { FaSpinner } from "react-icons/fa";
import { GoPlus } from "react-icons/go";
import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";
import { useUser } from "@/contexts/UserContext";
import { cn } from "@/libs/utils";

export interface AddBooksButtonProps {
  /**
   * Ref to attach to the hidden file input element.
   */
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  /**
   * Handler for file input change event.
   */
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  /**
   * Accepted file extensions for book formats.
   */
  accept: string;
  /**
   * Whether an upload is currently in progress.
   */
  isUploading?: boolean;
}

/**
 * Button component for adding books to the library.
 *
 * Displays a prominent button with a plus icon for adding new books.
 * Opens file browser when clicked to select book files.
 * Follows SRP by handling only UI concerns.
 * Follows IOC by accepting file input handlers as props.
 */
export function AddBooksButton({
  fileInputRef,
  onFileChange,
  accept,
  isUploading = false,
}: AddBooksButtonProps) {
  const { canPerformAction } = useUser();
  const { activeLibrary, selectedLibraryId, visibleLibraries } =
    useActiveLibrary();
  const canCreate = canPerformAction("books", "create");

  // Show a note when viewing a different library than the active (ingest) one
  const isViewingDifferentLibrary =
    visibleLibraries.length > 1 &&
    selectedLibraryId !== null &&
    activeLibrary !== null &&
    selectedLibraryId !== activeLibrary.id;

  const handleClick = () => {
    if (canCreate) {
      fileInputRef.current?.click();
    }
  };

  return (
    <div className="flex items-center gap-2">
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        multiple
        onChange={onFileChange}
        className="hidden"
        aria-label="Select book files"
      />
      <button
        type="button"
        className={cn(
          // Layout
          "flex cursor-pointer items-center gap-2 whitespace-nowrap",
          // Shape & spacing
          "h-[34px] rounded-md border-none px-3",
          // Colors
          "bg-primary-a0 text-[var(--color-text-primary-a0)]",
          // Typography
          "font-inherit font-medium text-sm",
          // Transitions
          "transition-[background-color_0.2s,opacity_0.2s,transform_0.1s]",
          // Hover - darker, more blue
          "hover:bg-[var(--clr-primary-a10)]",
          // Active
          "active:scale-[0.98] active:opacity-90",
          // Disabled
          "disabled:cursor-not-allowed disabled:opacity-50",
        )}
        onClick={handleClick}
        disabled={!canCreate || isUploading}
        aria-label="Add books"
      >
        {isUploading ? (
          <FaSpinner
            className="flex-shrink-0 animate-spin text-[var(--color-text-primary-a0)]"
            aria-hidden="true"
          />
        ) : (
          <GoPlus
            className="flex-shrink-0 text-[var(--color-text-primary-a0)] text-xl"
            aria-hidden="true"
          />
        )}
        <span className="leading-none">
          {isUploading ? "Uploading..." : "Add Books"}
        </span>
      </button>
      {isViewingDifferentLibrary && activeLibrary && (
        <span
          className="text-text-a30 text-xs"
          title={`Books will be added to ${activeLibrary.name}`}
        >
          Adding to {activeLibrary.name}
        </span>
      )}
    </div>
  );
}
