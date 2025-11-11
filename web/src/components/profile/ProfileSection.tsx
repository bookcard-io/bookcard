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
