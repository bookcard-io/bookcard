"use client";

import { ChangePasswordForm } from "./ChangePasswordForm";
import { EditableNameField } from "./EditableNameField";
import type { UserProfile } from "./hooks/useUserProfile";

interface UserDetailsProps {
  /**
   * User profile data to display.
   */
  user: UserProfile;
}

/**
 * User details component displaying profile information.
 *
 * Shows user's full name, username, email, and password change form.
 * Follows SRP by handling only user information display.
 */
export function UserDetails({ user }: UserDetailsProps) {
  return (
    <div className="flex flex-1 flex-col gap-4">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <div className="font-medium text-sm text-text-a20">Full Name</div>
          <EditableNameField currentName={user.full_name} />
        </div>

        <div className="flex flex-col gap-1">
          <div className="font-medium text-sm text-text-a20">Username</div>
          <div className="text-text-a0">{user.username}</div>
        </div>

        <div className="flex flex-col gap-1">
          <div className="font-medium text-sm text-text-a20">Email</div>
          <div className="text-text-a0">{user.email}</div>
        </div>
      </div>

      <div className="border-surface-a20 border-t pt-2">
        <ChangePasswordForm />
      </div>
    </div>
  );
}
