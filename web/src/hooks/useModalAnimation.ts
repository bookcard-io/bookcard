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

import { useCallback, useEffect, useRef, useState } from "react";

export interface UseModalAnimationResult {
  /** Whether the initial fade-in animation has completed. */
  hasAnimated: boolean;
  /** Whether the modal is currently shaking. */
  isShaking: boolean;
  /** Trigger shake animation. */
  triggerShake: () => void;
  /** Overlay animation style. */
  overlayStyle: React.CSSProperties | undefined;
  /** Modal container animation style. */
  containerStyle: React.CSSProperties | undefined;
}

/**
 * Custom hook for modal animation state management.
 *
 * Manages fade-in and shake animations for modal overlays and containers.
 * Follows SRP by handling only animation concerns.
 * Follows DRY by centralizing animation timing logic.
 *
 * Parameters
 * ----------
 * fadeInDuration : number
 *     Duration of fade-in animation in milliseconds. Defaults to 250ms.
 *     Should be slightly longer than CSS animation duration (200ms).
 *
 * Returns
 * -------
 * UseModalAnimationResult
 *     Object containing animation state and styles.
 */
export function useModalAnimation(
  fadeInDuration: number = 250,
): UseModalAnimationResult {
  const [hasAnimated, setHasAnimated] = useState(false);
  const [isShaking, setIsShaking] = useState(false);
  const hasAnimatedRef = useRef(false);

  // After the first mount, mark the fade-in as done so subsequent re-renders
  // (e.g. validation errors, shake) don't replay the overlay fade animation.
  useEffect(() => {
    if (hasAnimatedRef.current) {
      return;
    }
    const timer = setTimeout(() => {
      hasAnimatedRef.current = true;
      setHasAnimated(true);
    }, fadeInDuration);

    return () => clearTimeout(timer);
  }, [fadeInDuration]);

  const triggerShake = useCallback(() => {
    setIsShaking(true);
    setTimeout(() => {
      setIsShaking(false);
    }, 500);
  }, []);

  const overlayStyle: React.CSSProperties | undefined = hasAnimatedRef.current
    ? { animation: "none" }
    : undefined;

  const containerStyle: React.CSSProperties | undefined = hasAnimatedRef.current
    ? isShaking
      ? { animation: "shake 0.5s ease-in-out" }
      : { animation: "none" }
    : undefined;

  return {
    hasAnimated,
    isShaking,
    triggerShake,
    overlayStyle,
    containerStyle,
  };
}
