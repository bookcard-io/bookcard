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

import { useCallback, useState } from "react";
import { useFileDropzone } from "./useFileDropzone";

export interface ProfilePictureUploadOptions {
  /**
   * Callback function called when upload succeeds.
   */
  onUploadSuccess?: () => void;
  /**
   * Callback function called when upload fails.
   */
  onUploadError?: (error: string) => void;
}

/**
 * Custom hook for profile picture upload functionality.
 *
 * Wraps useFileDropzone with profile picture-specific configuration.
 * Handles file upload to backend and profile refresh.
 * Follows SRP by handling only profile picture upload concerns.
 * Follows IOC by accepting callbacks for upload results.
 *
 * Parameters
 * ----------
 * options : ProfilePictureUploadOptions
 *     Configuration options for profile picture upload.
 *
 * Returns
 * -------
 * ReturnType<typeof useFileDropzone> & { isUploading: boolean }
 *     File dropzone hook return value with profile picture configuration and upload state.
 */
export function useProfilePictureUpload(
  options: ProfilePictureUploadOptions = {},
) {
  const { onUploadSuccess, onUploadError } = options;
  const [isUploading, setIsUploading] = useState(false);

  const handleFileSelect = useCallback(
    async (file: File) => {
      // Validate file size (max 5MB)
      const maxSize = 5 * 1024 * 1024; // 5MB
      if (file.size > maxSize) {
        onUploadError?.("File size must be less than 5MB");
        return;
      }

      setIsUploading(true);

      try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch("/api/auth/profile-picture", {
          method: "POST",
          body: formData,
          credentials: "include",
        });

        if (!response.ok) {
          const data = (await response.json()) as { detail?: string };
          const errorMessage =
            data.detail || `Upload failed with status ${response.status}`;
          throw new Error(errorMessage);
        }

        onUploadSuccess?.();
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

  return {
    ...useFileDropzone({
      onFileSelect: handleFileSelect,
      accept:
        "image/jpeg,image/jpg,image/png,image/gif,image/webp,image/svg+xml",
      filterImages: true,
    }),
    isUploading,
  };
}
