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
  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        onChange={onFileChange}
        className="hidden"
        aria-label="Select book file"
      />
      <button
        type="button"
        className="flex cursor-pointer items-center gap-2 whitespace-nowrap rounded-lg border-none bg-primary-a0 px-5 py-2.5 font-inherit font-medium text-sm text-text-a0 transition-[background-color_0.2s,opacity_0.2s,transform_0.1s] hover:bg-primary-a10 active:scale-[0.98] active:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        onClick={handleClick}
        disabled={isUploading}
        aria-label="Add books"
      >
        <i
          className="pi pi-plus flex-shrink-0 text-text-a0"
          aria-hidden="true"
        />
        <span className="leading-none">
          {isUploading ? "Uploading..." : "Add Books"}
        </span>
      </button>
    </>
  );
}
