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
      <AddBooksButton
        fileInputRef={fileInputRef}
        onFileChange={onFileChange}
        accept={accept}
        isUploading={isUploading}
      />
    </PageHeader>
  );
}
