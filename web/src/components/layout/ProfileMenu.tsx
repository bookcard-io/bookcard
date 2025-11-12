"use client";

import { useCallback, useMemo } from "react";
import { DropdownMenu } from "@/components/common/DropdownMenu";
import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";
import type { User } from "@/contexts/UserContext";
import { useUser } from "@/contexts/UserContext";
import { getProfilePictureUrlWithCacheBuster } from "@/utils/profile";

export interface ProfileMenuProps {
  /** Whether the menu is open. */
  isOpen: boolean;
  /** Callback when menu should be closed. */
  onClose: () => void;
  /** Reference to the button element (for click outside detection). */
  buttonRef: React.RefObject<HTMLElement | null>;
  /** Cursor position when menu was opened. */
  cursorPosition: { x: number; y: number } | null;
  /** User data to display in header. */
  user: User | null;
  /** Callback when View profile is clicked. */
  onViewProfile?: () => void;
  /** Callback when Logout is clicked. */
  onLogout?: () => void;
}

/**
 * Profile dropdown menu component.
 *
 * Displays a dropdown menu with profile actions.
 * Follows SRP by handling only menu display and item selection.
 * Uses IOC via callback props for actions.
 * Follows DRY by using shared DropdownMenu and DropdownMenuItem components.
 */
export function ProfileMenu({
  isOpen,
  onClose,
  buttonRef,
  cursorPosition,
  user,
  onViewProfile,
  onLogout,
}: ProfileMenuProps) {
  const handleViewProfileClick = useCallback(() => {
    if (onViewProfile) {
      onViewProfile();
    }
    onClose();
  }, [onViewProfile, onClose]);

  const handleLogoutClick = useCallback(() => {
    if (onLogout) {
      onLogout();
    }
    onClose();
  }, [onLogout, onClose]);

  const displayName = user?.full_name ?? user?.username ?? "User";
  const { refreshTimestamp } = useUser();

  // Generate profile picture URL with cache-busting
  // Use refreshTimestamp to ensure image reloads on any user context refresh
  const profilePictureUrl = useMemo(() => {
    if (!user?.profile_picture) {
      return null;
    }
    return getProfilePictureUrlWithCacheBuster(refreshTimestamp);
  }, [user?.profile_picture, refreshTimestamp]);

  return (
    <DropdownMenu
      isOpen={isOpen}
      onClose={onClose}
      buttonRef={buttonRef}
      cursorPosition={cursorPosition}
      ariaLabel="Profile actions"
    >
      {/* Header section with profile picture and name */}
      <div className="bg-surface-tonal-a0 px-4 py-5">
        <button
          type="button"
          className="flex w-full cursor-pointer flex-col items-center gap-2 border-0 bg-transparent p-0 text-center"
          onClick={handleViewProfileClick}
          aria-label="View profile"
        >
          {/* Profile picture or placeholder */}
          {profilePictureUrl ? (
            <img
              src={profilePictureUrl}
              alt="Profile"
              className="h-16 w-16 rounded-full object-cover"
              key={profilePictureUrl}
            />
          ) : (
            <div className="relative flex h-16 w-16 items-center justify-center overflow-hidden rounded-full">
              {/* Muted, blurred circular background */}
              <div className="absolute inset-0 rounded-full bg-surface-tonal-a30 opacity-50 blur-xl" />
              {/* Icon - dead centered */}
              <i
                className="pi pi-user relative text-2xl text-text-a30"
                aria-hidden="true"
              />
            </div>
          )}
          {/* User name */}
          <span className="font-medium text-sm text-text-a0">
            {displayName}
          </span>
        </button>
      </div>
      {/* Menu items */}
      <DropdownMenuItem
        icon="pi pi-id-card"
        label="View profile"
        onClick={handleViewProfileClick}
        className="cursor-pointer"
      />
      <DropdownMenuItem
        icon="pi pi-sign-out"
        label="Logout"
        onClick={handleLogoutClick}
        className="cursor-pointer"
      />
    </DropdownMenu>
  );
}
