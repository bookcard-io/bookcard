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

import type { RefObject } from "react";
import { useEffect } from "react";
import type { ReactReader } from "react-reader";

/**
 * Hook to register TOC toggle handler with parent component.
 *
 * Creates a toggle function that calls the ReactReader's internal toggleToc
 * method and registers it with the parent via callback.
 *
 * Parameters
 * ----------
 * reactReaderRef : RefObject<ReactReader | null>
 *     Ref to the ReactReader component instance.
 * onTocToggle : ((handler: (() => void) | null) => void) | undefined
 *     Callback to register the toggle handler with parent.
 */
export function useTocToggle(
  reactReaderRef: RefObject<ReactReader | null>,
  onTocToggle?: (handler: (() => void) | null) => void,
) {
  useEffect(() => {
    if (!onTocToggle) {
      return;
    }

    const toggleToc = () => {
      // Call toggleToc method on ReactReader instance
      if (reactReaderRef.current?.toggleToc) {
        reactReaderRef.current.toggleToc();
      }
    };

    onTocToggle(toggleToc);

    return () => {
      onTocToggle(null);
    };
  }, [onTocToggle, reactReaderRef]);
}
