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

import { useCallback, useEffect, useRef, useState } from "react";
import { validateImageFile } from "@/utils/imageValidation";

export interface UseCoverFileOptions {
  /** Initial cover file (e.g., from book cover). */
  initialCoverFile?: File | null;
  /** Whether component is in edit mode. */
  isEditMode: boolean;
}

export interface UseCoverFileResult {
  /** Current cover file. */
  coverFile: File | null;
  /** Cover preview URL (object URL for new files). */
  coverPreviewUrl: string | null;
  /** Cover validation error message. */
  coverError: string | null;
  /** Whether cover deletion is staged. */
  isCoverDeleteStaged: boolean;
  /** File input ref. */
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  /** Handle file input change. */
  handleCoverFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  /** Clear cover file. */
  handleClearCoverFile: () => void;
  /** Stage cover deletion. */
  handleCoverDelete: () => void;
  /** Cancel staged deletion. */
  handleCancelDelete: () => void;
  /** Reset cover state. */
  reset: () => void;
}

/**
 * Custom hook for cover file management.
 *
 * Handles cover file state, validation, preview URL generation, and deletion staging.
 * Follows SRP by handling only cover file concerns.
 * Follows IOC by accepting initial values and providing callbacks.
 *
 * Parameters
 * ----------
 * options : UseCoverFileOptions
 *     Configuration options for cover file management.
 *
 * Returns
 * -------
 * UseCoverFileResult
 *     Object containing cover file state and handlers.
 */
export function useCoverFile(options: UseCoverFileOptions): UseCoverFileResult {
  const { initialCoverFile, isEditMode } = options;

  const [coverFile, setCoverFile] = useState<File | null>(
    initialCoverFile || null,
  );
  const [coverError, setCoverError] = useState<string | null>(null);
  const [isCoverDeleteStaged, setIsCoverDeleteStaged] = useState(false);
  const [coverPreviewUrl, setCoverPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const hasUserTouchedCoverRef = useRef(false);

  // Create object URL for cover preview and clean up on unmount or file change
  useEffect(() => {
    if (coverFile) {
      const objectUrl = URL.createObjectURL(coverFile);
      setCoverPreviewUrl(objectUrl);
      return () => {
        URL.revokeObjectURL(objectUrl);
      };
    }
    setCoverPreviewUrl(null);
    return () => {};
  }, [coverFile]);

  // Keep coverFile in sync with initialCoverFile for create mode,
  // but do not overwrite if the user has already interacted with the cover input.
  useEffect(() => {
    if (!isEditMode && initialCoverFile && !hasUserTouchedCoverRef.current) {
      setCoverFile((prev) => prev ?? initialCoverFile);
    }
  }, [initialCoverFile, isEditMode]);

  const handleCoverFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        const validation = validateImageFile(file);
        if (!validation.valid) {
          setCoverError(validation.error || "Invalid file");
          return;
        }
        setCoverFile(file);
        setCoverError(null);
        hasUserTouchedCoverRef.current = true;
        setIsCoverDeleteStaged(false);
      }
    },
    [],
  );

  const handleClearCoverFile = useCallback(() => {
    setCoverFile(null);
    setCoverError(null);
    setIsCoverDeleteStaged(false);
    hasUserTouchedCoverRef.current = true;
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, []);

  const handleCoverDelete = useCallback(() => {
    setIsCoverDeleteStaged(true);
    setCoverFile(null);
    setCoverError(null);
    hasUserTouchedCoverRef.current = true;
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, []);

  const handleCancelDelete = useCallback(() => {
    setIsCoverDeleteStaged(false);
  }, []);

  const reset = useCallback(() => {
    setCoverFile(null);
    setCoverError(null);
    setIsCoverDeleteStaged(false);
    hasUserTouchedCoverRef.current = false;
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, []);

  return {
    coverFile,
    coverPreviewUrl,
    coverError,
    isCoverDeleteStaged,
    fileInputRef,
    handleCoverFileChange,
    handleClearCoverFile,
    handleCoverDelete,
    handleCancelDelete,
    reset,
  };
}
