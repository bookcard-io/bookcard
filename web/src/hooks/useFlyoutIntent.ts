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

export interface UseFlyoutIntentOptions {
  /** Whether the flyout is currently open. */
  isOpen: boolean;
  /** Reference to the parent trigger element. */
  parentItemRef: React.RefObject<HTMLElement | null>;
  /** Reference to the flyout menu element. */
  menuRef: React.RefObject<HTMLElement | null>;
  /** Called when pointer leaves the padded union rect of parent + flyout. */
  onClose: () => void;
  /** Extra padding in pixels to expand the union hitbox. */
  padding?: number;
}

/**
 * Intent-aware hover guard for flyout menus.
 *
 * Keeps the flyout open while the pointer remains within the padded
 * union of the trigger element and the flyout menu, avoiding the need
 * for timers while supporting diagonal mouse movement.
 */
export function useFlyoutIntent({
  isOpen,
  parentItemRef,
  menuRef,
  onClose,
  padding = 10,
}: UseFlyoutIntentOptions) {
  const rafIdRef = useRef<number | null>(null);
  const pendingEventRef = useRef<PointerEvent | null>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handlePointerMove = (event: PointerEvent) => {
      pendingEventRef.current = event;

      if (rafIdRef.current !== null) {
        return;
      }

      rafIdRef.current = window.requestAnimationFrame(() => {
        rafIdRef.current = null;
        const e = pendingEventRef.current;
        if (!e) {
          return;
        }

        const parentEl = parentItemRef.current;
        const menuEl = menuRef.current;
        if (!parentEl || !menuEl) {
          // If either element is missing, close to avoid stuck state
          onClose();
          return;
        }

        const p = parentEl.getBoundingClientRect();
        const m = menuEl.getBoundingClientRect();

        const top = Math.min(p.top, m.top) - padding;
        const left = Math.min(p.left, m.left) - padding;
        const right = Math.max(p.right, m.right) + padding;
        const bottom = Math.max(p.bottom, m.bottom) + padding;

        const x = e.clientX;
        const y = e.clientY;

        const inside = x >= left && x <= right && y >= top && y <= bottom;

        if (!inside) {
          onClose();
        }
      });
    };

    window.addEventListener("pointermove", handlePointerMove, {
      passive: true,
    });
    window.addEventListener("scroll", handlePointerMove, true);
    window.addEventListener("resize", handlePointerMove);

    return () => {
      window.removeEventListener("pointermove", handlePointerMove as any);
      window.removeEventListener("scroll", handlePointerMove, true);
      window.removeEventListener("resize", handlePointerMove);
      if (rafIdRef.current !== null) {
        window.cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
      pendingEventRef.current = null;
    };
  }, [isOpen, parentItemRef, menuRef, onClose, padding]);
}
