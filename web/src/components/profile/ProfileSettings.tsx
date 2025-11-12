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

import { ConfigurationsSection } from "./ConfigurationsSection";
import { DevicesSection } from "./DevicesSection";
import { useUserProfile } from "./hooks/useUserProfile";
import { ProfileSection } from "./ProfileSection";

/**
 * Profile settings component.
 *
 * Displays user information, devices, and configuration preferences.
 * Follows SRP by delegating to specialized section components.
 */
export function ProfileSettings() {
  const { user, isLoading, error } = useUserProfile();

  if (isLoading) {
    return (
      <div className="p-6 px-8">
        <div className="text-text-a30">Loading profile...</div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="p-6 px-8">
        <div className="text-text-a30">Failed to load profile</div>
      </div>
    );
  }

  return (
    <div className="p-6 px-8">
      <div className="flex flex-col gap-8">
        <ProfileSection user={user} />
        <DevicesSection devices={user.ereader_devices} />
        <ConfigurationsSection />
      </div>
    </div>
  );
}
