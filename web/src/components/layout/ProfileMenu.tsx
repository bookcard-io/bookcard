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

import { useCallback } from "react";
import { DropdownMenu } from "@/components/common/DropdownMenu";
import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";
import type { User } from "@/contexts/UserContext";
import { useUser } from "@/contexts/UserContext";
import { useTheme } from "@/hooks/useTheme";

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
  // Use shared profile picture URL from context (fetched once globally)
  const { profilePictureUrl } = useUser();
  const { theme, toggleTheme } = useTheme();

  const handleThemeToggle = useCallback(() => {
    toggleTheme();
    onClose();
  }, [toggleTheme, onClose]);

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
        icon={theme === "dark" ? "pi pi-sun" : "pi pi-moon"}
        label={theme === "dark" ? "Light Theme" : "Dark Theme"}
        onClick={handleThemeToggle}
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
