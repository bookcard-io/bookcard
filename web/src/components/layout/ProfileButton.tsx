"use client";

import { useUser } from "@/contexts/UserContext";
import { HeaderActionButton } from "./HeaderActionButton";

/**
 * Profile button component for the header action bar.
 *
 * Displays user profile picture or default icon.
 * Follows SRP by only handling profile-specific rendering logic.
 * Follows DRY by using HeaderActionButton for common structure.
 */
export function ProfileButton() {
  const { user } = useUser();

  return (
    <HeaderActionButton
      href="/profile"
      tooltipText="View/edit profile"
      ariaLabel="Go to profile"
    >
      {user?.profile_picture ? (
        <img
          src={user.profile_picture}
          alt="Profile"
          className="h-full w-full object-cover"
        />
      ) : (
        <div className="relative flex h-full w-full items-center justify-center overflow-hidden">
          {/* Muted, blurred circular background */}
          <div className="absolute inset-0 rounded-full bg-surface-tonal-a20 opacity-50 blur-xl" />
          {/* Icon - dead centered */}
          <i
            className="pi pi-user relative text-text-a30 text-xl"
            aria-hidden="true"
          />
        </div>
      )}
    </HeaderActionButton>
  );
}
