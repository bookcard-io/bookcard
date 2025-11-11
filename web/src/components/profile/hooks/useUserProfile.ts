import { useEffect, useState } from "react";

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
 * Returns
 * -------
 * { user, isLoading, error }
 *     User profile data, loading state, and error state.
 */
export function useUserProfile() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const response = await fetch("/api/auth/me", {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
        });

        if (!response.ok) {
          throw new Error("Failed to fetch profile");
        }

        const data = await response.json();
        // Ensure ereader_devices is always an array
        setUser({
          ...data,
          ereader_devices: data.ereader_devices || [],
        });
      } catch (err) {
        setError(err instanceof Error ? err : new Error("Unknown error"));
      } finally {
        setIsLoading(false);
      }
    };

    void fetchProfile();
  }, []);

  return { user, isLoading, error };
}
