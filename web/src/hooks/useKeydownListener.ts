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

import { useEffect } from "react";
import type { KeydownEventTarget } from "@/types/eventTargets";

export type DefaultKeydownTarget = "window" | "document";

export interface KeydownListenerOptions {
  /** Whether to listen for keydown events (default: true). */
  enabled?: boolean;
  /**
   * Optional keydown event target.
   *
   * Notes
   * -----
   * If omitted, a default target is used when available.
   */
  target?: KeydownEventTarget | null;
  /**
   * Which global target to use when `target` is omitted (default: "window").
   *
   * Notes
   * -----
   * Prefer "window" for navigation-like behaviors.
   */
  defaultTarget?: DefaultKeydownTarget;
  /** Keydown handler. */
  onKeyDown: (e: KeyboardEvent) => void;
}

function resolveDefaultTarget(
  defaultTarget: DefaultKeydownTarget,
): KeydownEventTarget | null {
  if (typeof window === "undefined") return null;
  if (defaultTarget === "window")
    return window as unknown as KeydownEventTarget;
  return document as unknown as KeydownEventTarget;
}

/**
 * Subscribe to a keydown event target.
 *
 * Notes
 * -----
 * This hook isolates event subscription/unsubscription from domain-specific
 * navigation logic (SRP) and encourages dependency inversion via injected
 * targets (DIP).
 *
 * Parameters
 * ----------
 * options : KeydownListenerOptions
 *     Subscription options and keydown handler.
 */
export function useKeydownListener({
  enabled = true,
  target,
  defaultTarget = "window",
  onKeyDown,
}: KeydownListenerOptions): void {
  useEffect(() => {
    if (!enabled) return;

    const eventTarget = target ?? resolveDefaultTarget(defaultTarget);
    if (!eventTarget) return;

    eventTarget.addEventListener("keydown", onKeyDown);
    return () => eventTarget.removeEventListener("keydown", onKeyDown);
  }, [enabled, target, defaultTarget, onKeyDown]);
}
