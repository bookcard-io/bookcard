import { useRef, useState } from "react";

export interface FileDropzoneOptions {
  /**
   * Callback function called when a file is selected or dropped.
   */
  onFileSelect?: (file: File) => void;
  /**
   * Accepted file types (MIME types or extensions).
   * Defaults to image files.
   */
  accept?: string;
  /**
   * Whether to filter for image files only when dropping.
   * Defaults to true.
   */
  filterImages?: boolean;
}

export interface FileDropzoneReturn {
  /**
   * Ref to attach to the hidden file input element.
   */
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  /**
   * Whether a file is currently being dragged over the dropzone.
   */
  isDragging: boolean;
  /**
   * Accepted file types for the file input.
   */
  accept: string;
  /**
   * Opens the file browser dialog.
   */
  openFileBrowser: () => void;
  /**
   * Handlers for drag and drop events.
   */
  dragHandlers: {
    onDragEnter: (e: React.DragEvent) => void;
    onDragOver: (e: React.DragEvent) => void;
    onDragLeave: (e: React.DragEvent) => void;
    onDrop: (e: React.DragEvent) => void;
  };
  /**
   * Handler for file input change event.
   */
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  /**
   * Handler for click events to open file browser.
   */
  handleClick: () => void;
  /**
   * Handler for keyboard events (Enter/Space) to open file browser.
   */
  handleKeyDown: (e: React.KeyboardEvent) => void;
}

/**
 * Custom hook for file dropzone functionality.
 *
 * Provides drag-and-drop file upload capabilities with file browser fallback.
 * Follows SRP by handling only file selection and drag-and-drop logic.
 * Follows IOC by accepting callbacks for file processing.
 *
 * Parameters
 * ----------
 * options : FileDropzoneOptions
 *     Configuration options for the dropzone.
 *
 * Returns
 * -------
 * FileDropzoneReturn
 *     Object containing refs, state, and event handlers.
 */
export function useFileDropzone(
  options: FileDropzoneOptions = {},
): FileDropzoneReturn {
  const {
    onFileSelect,
    accept = "image/jpeg,image/jpg,image/png,image/gif,image/webp,image/svg+xml",
    filterImages = true,
  } = options;

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const processFile = (file: File) => {
    if (onFileSelect) {
      onFileSelect(file);
    }
  };

  const openFileBrowser = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
    // Reset input to allow selecting the same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    const file = filterImages
      ? files.find((f) => f.type.startsWith("image/"))
      : files[0];

    if (file) {
      processFile(file);
    }
  };

  const handleClick = () => {
    openFileBrowser();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openFileBrowser();
    }
  };

  return {
    fileInputRef,
    isDragging,
    accept,
    openFileBrowser,
    dragHandlers: {
      onDragEnter: handleDragEnter,
      onDragOver: handleDragOver,
      onDragLeave: handleDragLeave,
      onDrop: handleDrop,
    },
    handleFileChange,
    handleClick,
    handleKeyDown,
  };
}
