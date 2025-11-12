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

export interface ProfilePictureDeleteOptions {
  /**
   * Callback function called when delete succeeds.
   */
  onDeleteSuccess?: () => void;
  /**
   * Callback function called when delete fails.
   */
  onDeleteError?: (error: string) => void;
}

export interface ProfilePictureDeleteResult {
  /**
   * Whether a delete operation is in progress.
   */
  isDeleting: boolean;
  /**
   * Delete the profile picture.
   */
  deleteProfilePicture: () => Promise<void>;
}

/**
 * Custom hook for profile picture deletion functionality.
 *
 * Handles API call to delete profile picture and success/error callbacks.
 * Follows SRP by handling only profile picture deletion concerns.
 * Follows IOC by accepting callbacks for delete results.
 *
 * Parameters
 * ----------
 * options : ProfilePictureDeleteOptions
 *     Configuration options for profile picture deletion.
 *
 * Returns
 * -------
 * ProfilePictureDeleteResult
 *     Object containing deletion state and delete function.
 */
export function useProfilePictureDelete(
  options: ProfilePictureDeleteOptions = {},
): ProfilePictureDeleteResult {
  const { onDeleteSuccess, onDeleteError } = options;
  const [isDeleting, setIsDeleting] = useState(false);

  const deleteProfilePicture = useCallback(async () => {
    setIsDeleting(true);

    try {
      const response = await fetch("/api/auth/profile-picture", {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      });

      if (!response.ok) {
        const data = (await response.json()) as { detail?: string };
        throw new Error(data.detail || "Failed to delete profile picture");
      }

      onDeleteSuccess?.();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to delete profile picture";
      onDeleteError?.(errorMessage);
    } finally {
      setIsDeleting(false);
    }
  }, [onDeleteSuccess, onDeleteError]);

  return {
    isDeleting,
    deleteProfilePicture,
  };
}
