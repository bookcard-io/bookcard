"use client";

import { useCallback } from "react";
import { DropdownMenu } from "@/components/common/DropdownMenu";
import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";

export interface ProfileMenuProps {
  /** Whether the menu is open. */
  isOpen: boolean;
  /** Callback when menu should be closed. */
  onClose: () => void;
  /** Reference to the button element (for click outside detection). */
  buttonRef: React.RefObject<HTMLElement | null>;
  /** Cursor position when menu was opened. */
  cursorPosition: { x: number; y: number } | null;
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

  return (
    <DropdownMenu
      isOpen={isOpen}
      onClose={onClose}
      buttonRef={buttonRef}
      cursorPosition={cursorPosition}
      ariaLabel="Profile actions"
    >
      <DropdownMenuItem
        icon="pi pi-id-card"
        label="View profile"
        onClick={handleViewProfileClick}
      />
      <DropdownMenuItem
        icon="pi pi-sign-out"
        label="Logout"
        onClick={handleLogoutClick}
      />
    </DropdownMenu>
  );
}
