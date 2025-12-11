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

import { useRef } from "react";
import { Button } from "@/components/forms/Button";

/**
 * Props for AddFormatButton component.
 */
export interface AddFormatButtonProps {
  /** Whether button is disabled. */
  disabled?: boolean;
  /** Whether upload is in progress. */
  isUploading?: boolean;
  /** File change handler. */
  onFileChange: (file: File) => void;
}

/**
 * Add format button component for triggering file upload.
 *
 * Handles file input and triggers upload workflow.
 * Follows SRP by focusing solely on upload trigger UI.
 *
 * Parameters
 * ----------
 * props : AddFormatButtonProps
 *     Component props including handlers and state.
 */
export function AddFormatButton({
  disabled,
  isUploading,
  onFileChange,
}: AddFormatButtonProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileChange(file);
    }
    // Reset input
    e.target.value = "";
  };

  return (
    <>
      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        onChange={handleFileChange}
        onClick={(e) => {
          (e.target as HTMLInputElement).value = "";
        }}
      />
      <Button
        type="button"
        variant="ghost"
        size="small"
        disabled={disabled || isUploading}
        onClick={handleClick}
        className="!border-primary-a20 !text-primary-a20 hover:!text-primary-a20 w-full justify-start rounded-md hover:border-primary-a10 hover:bg-surface-a20 focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isUploading ? (
          <span className="pi pi-spinner pi-spin mr-2 text-primary-a20" />
        ) : (
          <span
            className="pi pi-plus mr-2 text-primary-a20"
            aria-hidden="true"
          />
        )}
        {isUploading ? "Uploading..." : "Add new format"}
      </Button>
    </>
  );
}
