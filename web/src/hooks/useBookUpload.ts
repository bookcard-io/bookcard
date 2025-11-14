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

import { useCallback, useRef, useState } from "react";

export interface UseBookUploadOptions {
  /**
   * Callback fired when a book is successfully uploaded.
   *
   * Parameters
   * ----------
   * bookId : number
   *     ID of the newly uploaded book.
   */
  onUploadSuccess?: (bookId: number) => void;
  /**
   * Callback fired when upload fails.
   *
   * Parameters
   * ----------
   * error : string
   *     Error message.
   */
  onUploadError?: (error: string) => void;
}

export interface UseBookUploadResult {
  /**
   * Ref to attach to the hidden file input element.
   */
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  /**
   * Whether an upload is currently in progress.
   */
  isUploading: boolean;
  /**
   * Opens the file browser dialog.
   */
  openFileBrowser: () => void;
  /**
   * Handler for file input change event.
   */
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  /**
   * Accepted file extensions for book formats.
   */
  accept: string;
}

/**
 * Custom hook for book upload functionality.
 *
 * Handles file selection, upload to server, and success/error callbacks.
 * Follows SRP by handling only book upload concerns.
 * Follows IOC by accepting callbacks for upload results.
 *
 * Parameters
 * ----------
 * options : UseBookUploadOptions
 *     Configuration options for book upload.
 *
 * Returns
 * -------
 * UseBookUploadResult
 *     Object containing refs, state, and event handlers.
 */
export function useBookUpload(
  options: UseBookUploadOptions = {},
): UseBookUploadResult {
  const { onUploadSuccess, onUploadError } = options;
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);

  /**
   * Uploads a book file to the server.
   *
   * Creates a fresh copy of the file to avoid stream locking issues
   * when the same file is selected multiple times.
   *
   * Parameters
   * ----------
   * file : File
   *     Book file to upload.
   */
  const uploadBook = useCallback(
    async (file: File) => {
      setIsUploading(true);

      try {
        // Create a fresh copy of the file to avoid stream locking issues
        // This is especially important when the same file is selected multiple times
        // The browser may reuse the File object with a locked stream
        const fileBuffer = await file.arrayBuffer();
        const freshFile = new File([fileBuffer], file.name, {
          type: file.type,
          lastModified: file.lastModified,
        });

        const formData = new FormData();
        formData.append("file", freshFile);

        const response = await fetch("/api/books/upload", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          let errorMessage = `Upload failed with status ${response.status}`;
          try {
            const data = (await response.json()) as { detail?: string };
            if (data.detail) {
              errorMessage = data.detail;
            }
          } catch {
            // If JSON parsing fails, use the default error message
          }
          throw new Error(errorMessage);
        }

        const data = (await response.json()) as { book_id: number };
        onUploadSuccess?.(data.book_id);
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Upload failed";
        onUploadError?.(errorMessage);
      } finally {
        setIsUploading(false);
      }
    },
    [onUploadSuccess, onUploadError],
  );

  const openFileBrowser = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        void uploadBook(file);
      }
      // Reset input to allow selecting the same file again
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    },
    [uploadBook],
  );

  // Supported Calibre formats: AZW, AZW3, AZW4, CBZ, CBR, CB7, CBC, CHM, DJVU, DOCX, EPUB, FB2, FBZ, HTML, HTMLZ, KEPUB, LIT, LRF, MOBI, ODT, PDF, PRC, PDB, PML, RB, RTF, SNB, TCR, TXT, TXTZ
  const accept =
    ".epub,.mobi,.azw,.azw3,.azw4,.cbz,.cbr,.cb7,.cbc,.chm,.djvu,.docx,.fb2,.fbz,.html,.htmlz,.kepub,.lit,.lrf,.odt,.pdf,.prc,.pdb,.pml,.rb,.rtf,.snb,.tcr,.txt,.txtz";

  return {
    fileInputRef,
    isUploading,
    openFileBrowser,
    handleFileChange,
    accept,
  };
}
