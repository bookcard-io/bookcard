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

import { HeaderActionButton } from "./HeaderActionButton";

/**
 * Admin button component for the header action bar.
 *
 * Displays admin settings button.
 * Follows SRP by only handling admin-specific rendering logic.
 * Follows DRY by using HeaderActionButton for common structure.
 */
export function AdminButton() {
  return (
    <HeaderActionButton
      href="/admin"
      tooltipText="Admin settings"
      ariaLabel="Go to admin settings"
    >
      <i className="pi pi-cog text-text-a30 text-xl" aria-hidden="true" />
    </HeaderActionButton>
  );
}
