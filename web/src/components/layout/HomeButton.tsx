"use client";

import { LibraryBuilding } from "@/icons/LibraryBuilding";
import { HeaderActionButton } from "./HeaderActionButton";

/**
 * Home button component for the header action bar.
 *
 * Displays home/library button with library building icon.
 * Follows SRP by only handling home-specific rendering logic.
 * Follows DRY by using HeaderActionButton for common structure.
 */
export function HomeButton() {
  return (
    <HeaderActionButton
      href="/"
      tooltipText="Go to the library"
      ariaLabel="Go to the library"
    >
      <LibraryBuilding className="text-text-a30 text-xl" />
    </HeaderActionButton>
  );
}
