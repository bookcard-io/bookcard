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

import { useUser } from "@/contexts/UserContext";
import { AdminButton } from "./AdminButton";
import { HomeButton } from "./HomeButton";
import { useRegisterHeaderButton } from "./hooks/useRegisterHeaderButton";
import { ProfileButton } from "./ProfileButton";

/**
 * Component that registers standard header action bar buttons.
 *
 * Automatically registers HomeButton and ProfileButton, and conditionally registers
 * AdminButton based on user permissions. This is the single place to manage which
 * buttons appear in the header action bar.
 *
 * Follows DRY by centralizing button registration logic.
 * Follows SRP by only handling button registration.
 * Follows IOC by using context for user data.
 * Follows SOC by delegating registration lifecycle to useRegisterHeaderButton hook.
 */
export function HeaderActionBarButtons() {
  const { user } = useUser();

  // Register home button
  useRegisterHeaderButton("home", <HomeButton />);

  // Register profile button (ProfileButton uses useUser internally and will update automatically)
  useRegisterHeaderButton("profile", <ProfileButton />);

  // Conditionally register admin button based on user permissions
  // Always call hook, but pass null element when user is not admin
  useRegisterHeaderButton("admin", user?.is_admin ? <AdminButton /> : null);

  return null;
}
