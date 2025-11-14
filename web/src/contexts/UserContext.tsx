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

"use client";

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  fetchSettings as apiFetchSettings,
  saveSetting as apiSaveSetting,
  type Setting,
} from "@/services/settingsApi";
import { getProfilePictureUrlWithCacheBuster } from "@/utils/profile";

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
  refreshTimestamp: number;
  // Optimistically update user without full refresh (avoids remounts)
  updateUser: (userData: Partial<User>) => void;
  // Shared profile picture URL (computed once, shared across all components)
  profilePictureUrl: string | null;
  // Invalidate profile picture cache (call after upload/delete)
  invalidateProfilePictureCache: () => void;
  // Settings as part of the single source of truth
  settings: Record<string, Setting>;
  isSaving: boolean;
  getSetting: (key: string) => string | null;
  updateSetting: (key: string, value: string) => void;
  // Get default e-reader device
  defaultDevice: EReaderDevice | null;
}

export const UserContext = createContext<UserContextType | undefined>(
  undefined,
);

/**
 * User context provider.
 *
 * Manages the current authenticated user's profile data.
 * Also manages user settings to act as the single source of truth for both.
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
  const [refreshTimestamp, setRefreshTimestamp] = useState(0);
  const [settings, setSettings] = useState<Record<string, Setting>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [profilePictureCacheBuster, setProfilePictureCacheBuster] = useState(
    Date.now(),
  );
  const hasInitialRefetchRunRef = useRef(false);
  const previousPicturePathRef = useRef<string | null>(null);

  // Queue for debounced settings updates
  const pendingUpdatesRef = useRef<Map<string, string>>(new Map());
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const DEFAULT_DEBOUNCE_MS = 300;

  const refresh = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch profile and settings concurrently
      const profilePromise = fetch("/api/auth/me", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      });
      const settingsPromise = apiFetchSettings();

      const [profileResponse, settingsResponse] = await Promise.all([
        profilePromise,
        settingsPromise,
      ]);

      if (!profileResponse.ok) {
        throw new Error("Failed to fetch user profile");
      }

      const data = await profileResponse.json();
      // Ensure ereader_devices is always an array
      const updatedUser = {
        ...data,
        ereader_devices: data.ereader_devices || [],
      };
      setUser(updatedUser);
      setSettings(settingsResponse.settings || {});

      // Update profile picture cache buster if picture path changed
      const currentPath = updatedUser.profile_picture ?? null;
      if (currentPath !== previousPicturePathRef.current) {
        setProfilePictureCacheBuster(Date.now());
        previousPicturePathRef.current = currentPath;
      }

      // Update refresh timestamp to force cache invalidation in all components
      setRefreshTimestamp(Date.now());
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown error"));
      setUser(null);
      setSettings({});
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Avoid duplicate fetch in React 18 StrictMode development double-invoke
    if (!hasInitialRefetchRunRef.current) {
      hasInitialRefetchRunRef.current = true;
      void refresh();
    }
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [refresh]);

  // Debounced save of pending settings updates
  const savePendingSettings = useCallback(async () => {
    const updates = pendingUpdatesRef.current;
    if (updates.size === 0) {
      return;
    }
    const updatesToSave = new Map(updates);
    pendingUpdatesRef.current.clear();
    setIsSaving(true);
    try {
      const promises = Array.from(updatesToSave.entries()).map(
        async ([key, value]) => {
          const setting = await apiSaveSetting(key, value);
          return { key, setting };
        },
      );
      const results = await Promise.all(promises);
      setSettings((prev) => {
        const updated = { ...prev };
        for (const { key, setting } of results) {
          updated[key] = setting;
        }
        return updated;
      });
    } catch (saveError) {
      // Re-queue on failure for retry; surface in console rather than breaking UX
      for (const [key, value] of updatesToSave.entries()) {
        pendingUpdatesRef.current.set(key, value);
      }
      // Preserve original error policy: do not throw here
      // eslint-disable-next-line no-console
      console.error("Failed to save settings:", saveError);
    } finally {
      setIsSaving(false);
    }
  }, []);

  const scheduleSettingsSave = useCallback(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    debounceTimerRef.current = setTimeout(() => {
      void savePendingSettings();
    }, DEFAULT_DEBOUNCE_MS);
  }, [savePendingSettings]);

  const updateSetting = useCallback(
    (key: string, value: string) => {
      // Optimistically update local SSOT
      setSettings((prev) => ({
        ...prev,
        [key]: {
          key,
          value,
          description: prev[key]?.description,
          updated_at: new Date().toISOString(),
        },
      }));
      // Queue persistence
      pendingUpdatesRef.current.set(key, value);
      scheduleSettingsSave();
    },
    [scheduleSettingsSave],
  );

  const getSetting = useCallback(
    (key: string): string | null => {
      return settings[key]?.value ?? null;
    },
    [settings],
  );

  /**
   * Optimistically update user state without triggering full refresh.
   * Prevents unnecessary remounts when only user profile data changes.
   * Does not update refreshTimestamp or refetch settings.
   */
  const updateUser = useCallback((userData: Partial<User>) => {
    setUser((prev) => {
      if (!prev) {
        return prev;
      }
      const updated = { ...prev, ...userData };
      // Update profile picture cache buster if picture path changed
      const currentPath = updated.profile_picture ?? null;
      if (currentPath !== previousPicturePathRef.current) {
        setProfilePictureCacheBuster(Date.now());
        previousPicturePathRef.current = currentPath;
      }
      return updated;
    });
  }, []);

  /**
   * Invalidate profile picture cache.
   * Call this after uploading or deleting a profile picture to force reload.
   */
  const invalidateProfilePictureCache = useCallback(() => {
    setProfilePictureCacheBuster(Date.now());
  }, []);

  // Compute shared profile picture URL once
  const profilePictureUrl = useMemo(() => {
    if (!user?.profile_picture) {
      return null;
    }
    return getProfilePictureUrlWithCacheBuster(profilePictureCacheBuster);
  }, [user?.profile_picture, profilePictureCacheBuster]);

  // Get default e-reader device
  const defaultDevice = useMemo(() => {
    if (!user?.ereader_devices || user.ereader_devices.length === 0) {
      return null;
    }
    return user.ereader_devices.find((device) => device.is_default) || null;
  }, [user?.ereader_devices]);

  const contextValue = useMemo(
    () => ({
      user,
      isLoading,
      error,
      refresh,
      refreshTimestamp,
      updateUser,
      profilePictureUrl,
      invalidateProfilePictureCache,
      settings,
      isSaving,
      getSetting,
      updateSetting,
      defaultDevice,
    }),
    [
      user,
      isLoading,
      error,
      refresh,
      refreshTimestamp,
      updateUser,
      profilePictureUrl,
      invalidateProfilePictureCache,
      settings,
      isSaving,
      getSetting,
      updateSetting,
      defaultDevice,
    ],
  );

  return (
    <UserContext.Provider value={contextValue}>{children}</UserContext.Provider>
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
