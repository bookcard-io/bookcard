import { useCallback, useState } from "react";
import { useUser } from "@/contexts/UserContext";

export interface ProfileUpdatePayload {
  username?: string;
  email?: string;
  full_name?: string | null;
}

export interface UseProfileUpdateOptions {
  /**
   * Callback function called when update succeeds.
   */
  onUpdateSuccess?: () => void;
  /**
   * Callback function called when update fails.
   */
  onUpdateError?: (error: string) => void;
}

/**
 * Custom hook for profile update functionality.
 *
 * Handles updating user profile information (username, email, full_name).
 * Automatically refreshes user context after successful update.
 * Follows SRP by handling only profile update concerns.
 * Follows IOC by accepting callbacks for update results.
 *
 * Parameters
 * ----------
 * options : UseProfileUpdateOptions
 *     Configuration options for profile updates.
 *
 * Returns
 * -------
 * { updateProfile, isUpdating, error }
 *     Profile update function, loading state, and error state.
 */
export function useProfileUpdate(options: UseProfileUpdateOptions = {}): {
  updateProfile: (payload: ProfileUpdatePayload) => Promise<void>;
  isUpdating: boolean;
  error: string | null;
} {
  const { onUpdateSuccess, onUpdateError } = options;
  const { refresh } = useUser();
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateProfile = useCallback(
    async (payload: ProfileUpdatePayload) => {
      setIsUpdating(true);
      setError(null);

      try {
        const response = await fetch("/api/auth/profile", {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
          credentials: "include",
        });

        if (!response.ok) {
          const data = (await response.json()) as { detail?: string };
          const errorMessage =
            data.detail || `Update failed with status ${response.status}`;
          throw new Error(errorMessage);
        }

        // Refresh user context to get updated data
        await refresh();
        onUpdateSuccess?.();
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Update failed";
        setError(errorMessage);
        onUpdateError?.(errorMessage);
      } finally {
        setIsUpdating(false);
      }
    },
    [refresh, onUpdateSuccess, onUpdateError],
  );

  return { updateProfile, isUpdating, error };
}
