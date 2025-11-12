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

import type { ReactNode } from "react";
import { HeaderActionBar } from "./HeaderActionBar";

export interface PageHeaderProps {
  /**
   * Title to display on the left side of the header.
   */
  title: ReactNode;
  /**
   * Optional additional content to display between title and action bar.
   */
  children?: ReactNode;
}

/**
 * Reusable page header component.
 *
 * Displays a title on the left and the header action bar on the right.
 * Follows DRY by providing consistent header layout across pages.
 * Follows SRP by only handling header layout.
 *
 * Parameters
 * ----------
 * props : PageHeaderProps
 *     Component props including title and optional children.
 *
 * Examples
 * --------
 * ```tsx
 * <PageHeader title="My Library">
 *   <AddBooksButton />
 * </PageHeader>
 * ```
 */
export function PageHeader({ title, children }: PageHeaderProps) {
  return (
    <header className="flex items-center justify-between px-8 pt-6 pb-4">
      <h1 className="m-0 font-semibold text-[32px] text-[var(--color-text-a0)] leading-[1.2]">
        {title}
      </h1>
      <div className="flex shrink-0 items-center gap-3">
        {children}
        <HeaderActionBar />
      </div>
    </header>
  );
}
