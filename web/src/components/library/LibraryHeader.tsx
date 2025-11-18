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

import { PageHeader } from "@/components/layout/PageHeader";
import { AddBooksButton } from "./widgets/AddBooksButton";

export interface LibraryHeaderProps {
  /**
   * Callback fired when "Add Books" button is clicked.
   */
  onAddBooksClick?: () => void;
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
 * Header component for the library page.
 *
 * Displays the "My Library" title at the top of the main content area
 * with the "Add Books" button positioned on the right.
 * Standard action bar buttons (Profile, Admin) are automatically included
 * via the HeaderActionBarButtons component in PageLayout.
 * Follows IOC by accepting file upload handlers as props.
 */
export function LibraryHeader({
  fileInputRef,
  onFileChange,
  accept,
  isUploading,
}: LibraryHeaderProps) {
  return (
    <PageHeader title="My Library">
      <div className="flex items-center gap-3">
        <AddBooksButton
          fileInputRef={fileInputRef}
          onFileChange={onFileChange}
          accept={accept}
          isUploading={isUploading}
        />
      </div>
    </PageHeader>
  );
}
