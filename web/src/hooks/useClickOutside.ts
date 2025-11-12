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

import { useEffect, useRef } from "react";

/**
 * Custom hook for detecting clicks outside a component.
 *
 * Parameters
 * ----------
 * handler : () => void
 *     Callback function to execute when click outside is detected.
 * enabled : boolean
 *     Whether the click outside detection is enabled (default: true).
 *
 * Returns
 * -------
 * React.RefObject<T>
 *     Ref object to attach to the element to monitor.
 */
export function useClickOutside<T extends HTMLElement = HTMLDivElement>(
  handler: () => void,
  enabled: boolean = true,
): React.RefObject<T | null> {
  const ref = useRef<T | null>(null);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        handler();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [handler, enabled]);

  return ref;
}
