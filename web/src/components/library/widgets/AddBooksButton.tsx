"use client";

import styles from "./AddBooksButton.module.scss";

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
        style={{ display: "none" }}
        aria-label="Select book file"
      />
      <button
        type="button"
        className={styles.addBooksButton}
        onClick={handleClick}
        disabled={isUploading}
        aria-label="Add books"
      >
        <i className="pi pi-plus" aria-hidden="true" />
        <span className={styles.buttonText}>
          {isUploading ? "Uploading..." : "Add Books"}
        </span>
      </button>
    </>
  );
}
