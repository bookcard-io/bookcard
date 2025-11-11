"use client";

import Link from "next/link";
import { useUser } from "@/contexts/UserContext";
import { AddBooksButton } from "./widgets/AddBooksButton";

export interface LibraryHeaderProps {
  /**
   * Callback fired when "Add Books" button is clicked.
   */
  onAddBooksClick?: () => void;
}

/**
 * Header component for the library page.
 *
 * Displays the "My Library" title at the top of the main content area
 * with the "Add Books" button positioned on the right.
 */
export function LibraryHeader({ onAddBooksClick }: LibraryHeaderProps) {
  const { user } = useUser();

  return (
    <header className="flex items-center justify-between px-8 pt-6 pb-4">
      <h1 className="m-0 font-semibold text-[32px] text-[var(--color-text-a0)] leading-[1.2]">
        My Library
      </h1>
      <div className="flex shrink-0 items-center gap-3">
        <AddBooksButton onClick={onAddBooksClick} />
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
      </div>
    </header>
  );
}
