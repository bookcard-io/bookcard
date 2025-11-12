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

import type { UserProfile } from "./hooks/useUserProfile";
import { ProfilePicture } from "./ProfilePicture";
import { UserDetails } from "./UserDetails";

interface ProfileSectionProps {
  /**
   * User profile data to display.
   */
  user: UserProfile;
}

/**
 * Profile section component.
 *
 * Orchestrates the display of profile picture and user details.
 * Follows SRP by delegating to specialized components.
 * Follows SOC by separating picture and details concerns.
 */
export function ProfileSection({ user }: ProfileSectionProps) {
  return (
    <div className="flex flex-col gap-6">
      <h2 className="m-0 font-semibold text-text-a0 text-xl">Profile</h2>

      <div className="flex flex-col gap-6 md:flex-row">
        <ProfilePicture />
        <UserDetails user={user} />
      </div>
    </div>
  );
}
