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

import { useCallback, useState } from "react";

export interface UseShelfCardAnimationResult {
  /** Whether the card is currently shaking. */
  isShaking: boolean;
  /** Whether the card is currently glowing. */
  isGlowing: boolean;
  /** Trigger shake and glow animation. */
  triggerAnimation: () => void;
}

/**
 * Custom hook for shelf card animation state.
 *
 * Manages shake and glow animation states with automatic cleanup.
 * Follows SRP by handling only animation concerns.
 * Follows DRY by centralizing animation timing logic.
 *
 * Returns
 * -------
 * UseShelfCardAnimationResult
 *     Object containing animation state and trigger function.
 */
export function useShelfCardAnimation(): UseShelfCardAnimationResult {
  const [isShaking, setIsShaking] = useState(false);
  const [isGlowing, setIsGlowing] = useState(false);

  const triggerAnimation = useCallback(() => {
    setIsShaking(true);
    setIsGlowing(true);
    // Reset shake after animation completes
    setTimeout(() => {
      setIsShaking(false);
    }, 500);
    // Fade out red glow after shake completes
    setTimeout(() => {
      setIsGlowing(false);
    }, 1000);
  }, []);

  return {
    isShaking,
    isGlowing,
    triggerAnimation,
  };
}
