"use client";

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

export interface EReaderDevice {
  id: number;
  user_id: number;
  email: string;
  device_name: string | null;
  device_type: string;
  is_default: boolean;
  preferred_format: string | null;
}

export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string | null;
  profile_picture: string | null;
  is_admin: boolean;
  ereader_devices?: EReaderDevice[];
}

interface UserContextType {
  user: User | null;
  isLoading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

/**
 * User context provider.
 *
 * Manages the current authenticated user's profile data.
 * Fetches user information from the backend and provides it to child components.
 * Follows SRP by handling only user profile data management.
 *
 * Parameters
 * ----------
 * children : ReactNode
 *     Child components that can access the user context.
 */
export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const refresh = useCallback(async () => {
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
        throw new Error("Failed to fetch user profile");
      }

      const data = await response.json();
      // Ensure ereader_devices is always an array
      setUser({
        ...data,
        ereader_devices: data.ereader_devices || [],
      });
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown error"));
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <UserContext.Provider value={{ user, isLoading, error, refresh }}>
      {children}
    </UserContext.Provider>
  );
}

/**
 * Hook to access user context.
 *
 * Returns
 * -------
 * UserContextType
 *     User context containing user data, loading state, error state, and refresh function.
 *
 * Raises
 * ------
 * Error
 *     If used outside of UserProvider.
 */
export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return context;
}
