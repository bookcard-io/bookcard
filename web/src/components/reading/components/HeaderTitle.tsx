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

/**
 * Header title component.
 *
 * Follows SRP by focusing solely on title display.
 * Follows SOC by separating title rendering from header layout.
 *
 * Parameters
 * ----------
 * title : string | null
 *     Book title to display.
 */
export function HeaderTitle({ title }: { title: string | null }) {
  return (
    <div className="-translate-x-1/2 absolute left-1/2">
      <h1 className="max-w-4xl truncate font-medium text-lg text-text-a0">
        {title || "Loading..."}
      </h1>
    </div>
  );
}
