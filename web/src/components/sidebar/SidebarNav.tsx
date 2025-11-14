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

import type { ReactNode } from "react";
import { cn } from "@/libs/utils";

export interface SidebarNavProps {
  /** Whether the nav is currently scrolling. */
  isScrolling: boolean;
  /** Ref to attach to the nav element. */
  navRef: React.RefObject<HTMLElement | null>;
  /** Child components to render inside the nav. */
  children: ReactNode;
}

/**
 * Sidebar navigation container component.
 *
 * Wraps sidebar navigation sections with scroll behavior.
 * Follows SRP by handling only nav container rendering.
 * Follows IOC by accepting children and refs via props.
 *
 * Parameters
 * ----------
 * props : SidebarNavProps
 *     Component props.
 */
export function SidebarNav({ isScrolling, navRef, children }: SidebarNavProps) {
  return (
    <nav
      ref={navRef}
      className={cn(
        "scrollbar-hide-on-idle flex-1 overflow-y-auto py-4",
        isScrolling && "scrolling",
      )}
    >
      {children}
    </nav>
  );
}
