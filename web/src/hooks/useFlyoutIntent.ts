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
  /**
   * Minimum pointer movement (in CSS pixels) between animation frames to
   * consider the pointer "moving with intent".
   *
   * If the pointer is effectively stationary within the safe corridor but
   * outside both the parent and flyout elements, the flyout will close.
   */
  minMovementPx?: number;
  /**
   * Minimum time delta (in milliseconds) between pointer events before
   * considering the pointer "stationary" for intent purposes.
   */
  idleTimeMs?: number;
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
  minMovementPx = 2,
  idleTimeMs = 100,
}: UseFlyoutIntentOptions) {
  const rafIdRef = useRef<number | null>(null);
  const pendingEventRef = useRef<PointerEvent | null>(null);
  const lastEventRef = useRef<PointerEvent | null>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handlePointerMove = (event: Event) => {
      // Only process PointerEvent for pointermove, but accept Event for scroll/resize
      const pointerEvent = event instanceof PointerEvent ? event : null;
      if (pointerEvent) {
        pendingEventRef.current = pointerEvent;
      }

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

        const insideCorridor =
          x >= left && x <= right && y >= top && y <= bottom;

        if (!insideCorridor) {
          onClose();
          lastEventRef.current = null;
          return;
        }

        // Within the safe corridor; detect when the pointer effectively
        // "comes to rest" on another menu item (outside parent/flyout)
        // and close in that case to avoid the flyout feeling sticky.
        const inParent =
          x >= p.left && x <= p.right && y >= p.top && y <= p.bottom;
        const inMenu =
          x >= m.left && x <= m.right && y >= m.top && y <= m.bottom;

        const prev = lastEventRef.current;
        lastEventRef.current = e;

        if (!inParent && !inMenu && prev) {
          const dt = e.timeStamp - prev.timeStamp;
          const dx = e.clientX - prev.clientX;
          const dy = e.clientY - prev.clientY;
          const distance = Math.hypot(dx, dy);

          const isStationary = dt >= idleTimeMs && distance < minMovementPx;

          if (isStationary) {
            onClose();
            lastEventRef.current = null;
          }
        }
      });
    };

    window.addEventListener("pointermove", handlePointerMove, {
      passive: true,
    });
    window.addEventListener("scroll", handlePointerMove, true);
    window.addEventListener("resize", handlePointerMove);

    return () => {
      // Options are not needed for removeEventListener, but we include them for type matching
      window.removeEventListener("pointermove", handlePointerMove, {
        passive: true,
      } as AddEventListenerOptions);
      window.removeEventListener("scroll", handlePointerMove, true);
      window.removeEventListener("resize", handlePointerMove);
      if (rafIdRef.current !== null) {
        window.cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
      pendingEventRef.current = null;
    };
  }, [
    isOpen,
    parentItemRef,
    menuRef,
    onClose,
    padding,
    minMovementPx,
    idleTimeMs,
  ]);
}
