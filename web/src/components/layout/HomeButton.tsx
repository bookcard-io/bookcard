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
