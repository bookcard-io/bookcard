import type { User } from "@/contexts/UserContext";
import { useUser } from "@/contexts/UserContext";

export interface EReaderDevice {
  id: number;
  user_id: number;
  email: string;
  device_name: string | null;
  device_type: string;
  is_default: boolean;
  preferred_format: string | null;
}

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  full_name?: string | null;
  profile_picture: string | null;
  is_admin: boolean;
  ereader_devices?: EReaderDevice[];
}

/**
 * Hook to fetch and manage user profile data.
 *
 * Delegates to UserContext, the single source of truth for user data.
 * Automatically reflects updates when the context refreshes.
 *
 * Returns
 * -------
 * { user, isLoading, error }
 *     User profile data, loading state, and error state.
 */
export function useUserProfile() {
  const { user, isLoading, error } = useUser();
  return {
    user: user as unknown as UserProfile | User | null,
    isLoading,
    error,
  };
}
