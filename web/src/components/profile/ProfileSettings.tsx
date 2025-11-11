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
