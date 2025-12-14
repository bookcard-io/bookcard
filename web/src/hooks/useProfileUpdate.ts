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
import { type User, useUser } from "@/contexts/UserContext";

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
  const { updateUser } = useUser();
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

        // Get updated user data from response
        const updatedUser = (await response.json()) as User;

        // Optimistically update user state without full refresh
        // This prevents remounts and jitters in other components
        // Only update fields that were potentially changed
        // Preserve ereader_devices if not present in response (ProfileRead doesn't include it)
        const updateData: Partial<User> = {
          username: updatedUser.username,
          email: updatedUser.email,
          full_name: updatedUser.full_name,
          profile_picture: updatedUser.profile_picture,
          is_admin: updatedUser.is_admin,
        };

        // Only update ereader_devices if it's present in the response
        // Otherwise preserve the existing devices from current user state
        if (updatedUser.ereader_devices !== undefined) {
          updateData.ereader_devices = updatedUser.ereader_devices || [];
        }

        updateUser(updateData);

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
    [updateUser, onUpdateSuccess, onUpdateError],
  );

  return { updateProfile, isUpdating, error };
}
