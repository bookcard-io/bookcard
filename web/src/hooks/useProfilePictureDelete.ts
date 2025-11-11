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
