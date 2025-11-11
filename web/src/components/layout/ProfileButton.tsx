"use client";

import Link from "next/link";
import { useUser } from "@/contexts/UserContext";
import { Tooltip } from "./Tooltip";

/**
 * Profile button component for the header action bar.
 *
 * Displays user profile picture or default icon.
 * Follows SRP by only handling profile button rendering.
 */
export function ProfileButton() {
  const { user } = useUser();

  return (
    <Tooltip text="View profile">
      <Link
        href="/profile"
        className="flex h-[34px] w-[34px] shrink-0 items-center justify-center overflow-hidden rounded-full border border-surface-a20 bg-surface-tonal-a10 transition-colors duration-200 hover:bg-surface-tonal-a20"
        aria-label="Go to profile"
      >
        {user?.profile_picture ? (
          <img
            src={user.profile_picture}
            alt="Profile"
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="relative flex h-full w-full items-center justify-center">
            {/* Muted, blurred circular background */}
            <div className="absolute inset-0 rounded-full bg-surface-tonal-a20 opacity-50 blur-xl" />
            {/* Icon - dead centered */}
            <i
              className="pi pi-user relative text-text-a30 text-xl"
              aria-hidden="true"
            />
          </div>
        )}
      </Link>
    </Tooltip>
  );
}
