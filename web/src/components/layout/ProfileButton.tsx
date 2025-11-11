"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "@/contexts/UserContext";
import { Tooltip } from "./Tooltip";
import { ProfileMenu } from "./ProfileMenu";

/**
 * Profile button component for the header action bar.
 *
 * Displays user profile picture or default icon with dropdown menu.
 * Follows SRP by only handling profile-specific rendering logic.
 */
export function ProfileButton() {
  const { user } = useUser();
  const router = useRouter();
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [cursorPosition, setCursorPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);

  const handleButtonClick = useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    if (isMenuOpen) {
      setIsMenuOpen(false);
      setCursorPosition(null);
    } else {
      const rect = e.currentTarget.getBoundingClientRect();
      setCursorPosition({
        x: rect.right,
        y: rect.bottom,
      });
      setIsMenuOpen(true);
    }
  }, [isMenuOpen]);

  const handleCloseMenu = useCallback(() => {
    setIsMenuOpen(false);
    setCursorPosition(null);
  }, []);

  const handleViewProfile = useCallback(() => {
    router.push("/profile");
  }, [router]);

  const handleLogout = useCallback(async () => {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
      // Redirect to login page
      router.push("/login");
      router.refresh();
    } catch {
      // Even if logout fails, redirect to login
      router.push("/login");
      router.refresh();
    }
  }, [router]);

  return (
    <>
      <Tooltip text="View/edit profile">
        <button
          ref={buttonRef}
          type="button"
          onClick={handleButtonClick}
          className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-full border border-surface-a20 bg-surface-tonal-a10 transition-colors duration-200 hover:bg-surface-tonal-a20"
          aria-label="Profile menu"
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
        </button>
      </Tooltip>
      <ProfileMenu
        isOpen={isMenuOpen}
        onClose={handleCloseMenu}
        buttonRef={buttonRef}
        cursorPosition={cursorPosition}
        onViewProfile={handleViewProfile}
        onLogout={handleLogout}
      />
    </>
  );
}
