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

import { useCallback, useRef, useState } from "react";
import { useUser } from "@/contexts/UserContext";
import { ProfileMenu } from "./ProfileMenu";
import { Tooltip } from "./Tooltip";

/**
 * Profile button component for the header action bar.
 *
 * Displays user profile picture or default icon with dropdown menu.
 * Follows SRP by only handling profile-specific rendering logic.
 */
export function ProfileButton() {
  const { user } = useUser();
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [cursorPosition, setCursorPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);

  const handleButtonClick = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>) => {
      e.stopPropagation();
      if (isMenuOpen) {
        setIsMenuOpen(false);
        setCursorPosition(null);
      } else {
        // Capture cursor position from mouse event
        setCursorPosition({
          x: e.clientX,
          y: e.clientY,
        });
        setIsMenuOpen(true);
      }
    },
    [isMenuOpen],
  );

  const handleCloseMenu = useCallback(() => {
    setIsMenuOpen(false);
    setCursorPosition(null);
  }, []);

  // Use shared profile picture URL from context (fetched once globally)
  const { profilePictureUrl } = useUser();

  return (
    <>
      <div className="flex items-center gap-1">
        <Tooltip text="Account menu">
          <button
            ref={buttonRef}
            type="button"
            onClick={handleButtonClick}
            className="flex h-[34px] w-[34px] shrink-0 cursor-pointer items-center justify-center rounded-full border border-surface-a20 bg-surface-tonal-a10 transition-colors duration-200 hover:bg-surface-tonal-a20"
            aria-label="Account menu"
          >
            {profilePictureUrl ? (
              <img
                src={profilePictureUrl}
                alt="Profile"
                className="h-full w-full rounded-full object-cover"
                key={profilePictureUrl}
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
        <i
          className={`pi ${isMenuOpen ? "pi-chevron-up" : "pi-chevron-down"} text-sm text-text-a30 transition-transform duration-200`}
          aria-hidden="true"
        />
      </div>
      <ProfileMenu
        isOpen={isMenuOpen}
        onClose={handleCloseMenu}
        buttonRef={buttonRef}
        cursorPosition={cursorPosition}
        user={user}
      />
    </>
  );
}
