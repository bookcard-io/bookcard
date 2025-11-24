// Copyright (C) 2025 khoa and others
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

import type { NavItem } from "epubjs";
import { useMemo, useRef } from "react";

/**
 * Hook to track TOC changes.
 *
 * Follows SRP by focusing solely on TOC tracking.
 * Follows IOC by providing a reusable hook interface.
 *
 * Returns
 * -------
 * object
 *     Object containing TOC ref and change handler.
 */
export function useTocTracking() {
  const tocRef = useRef<NavItem[]>([]);

  const handleTocChanged = useMemo(
    () => (toc: NavItem[]) => {
      tocRef.current = toc;
    },
    [],
  );

  return {
    tocRef,
    handleTocChanged,
  };
}
