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

import { useState } from "react";
import { useProfileUpdate } from "@/hooks/useProfileUpdate";
import { ChangePasswordForm } from "./ChangePasswordForm";
import { EditableNameField, EditableTextField } from "./EditableNameField";
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
  const [updateError, setUpdateError] = useState<string | null>(null);
  const { updateProfile } = useProfileUpdate({
    onUpdateSuccess: () => {
      setUpdateError(null);
    },
    onUpdateError: (error) => {
      setUpdateError(error);
    },
  });

  const handleFullNameSave = async (fullName: string) => {
    await updateProfile({ full_name: fullName || null });
  };

  const handleUsernameSave = async (username: string) => {
    if (!username.trim()) {
      setUpdateError("Username cannot be empty");
      return;
    }
    await updateProfile({ username: username.trim() });
  };

  const handleEmailSave = async (email: string) => {
    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setUpdateError("Email cannot be empty");
      return;
    }
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(trimmedEmail)) {
      setUpdateError("Please enter a valid email address");
      return;
    }
    await updateProfile({ email: trimmedEmail });
  };

  return (
    <div className="flex flex-1 flex-col gap-4">
      {updateError && (
        <div className="rounded border border-error-a20 bg-error-tonal-a10 px-3 py-2 text-error-a0 text-sm">
          {updateError}
        </div>
      )}
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <div className="font-medium text-sm text-text-a20">Full Name</div>
          <EditableNameField
            currentName={user.full_name}
            onSave={handleFullNameSave}
          />
        </div>

        <div className="flex flex-col gap-1">
          <div className="font-medium text-sm text-text-a20">Username</div>
          <EditableTextField
            currentValue={user.username}
            placeholder="Enter your username"
            editLabel="Edit username"
            allowEmpty={false}
            onSave={handleUsernameSave}
          />
        </div>

        <div className="flex flex-col gap-1">
          <div className="font-medium text-sm text-text-a20">Email</div>
          <EditableTextField
            currentValue={user.email}
            placeholder="Enter your email"
            editLabel="Edit email"
            allowEmpty={false}
            onSave={handleEmailSave}
          />
        </div>
      </div>

      <div className="border-surface-a20 border-t pt-2">
        <ChangePasswordForm />
      </div>
    </div>
  );
}
