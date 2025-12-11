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
  serial_number?: string | null;
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
